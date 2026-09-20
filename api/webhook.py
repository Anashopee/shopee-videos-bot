import os
import json
import re
import urllib.request

import requests
from fastapi import FastAPI, Request


app = FastAPI()


# ============================================================
# CONFIGURAÇÕES
# ============================================================

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# Remove uma possível / no final para evitar URLs duplicadas
SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")

SUPABASE_SECRET_KEY = os.environ["SUPABASE_SECRET_KEY"]


# ============================================================
# TELEGRAM
# ============================================================

def enviar_mensagem(chat_id, texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    dados = json.dumps({
        "chat_id": chat_id,
        "text": texto
    }).encode("utf-8")

    requisicao = urllib.request.Request(
        url,
        data=dados,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(requisicao) as resposta:
        resposta.read()


# ============================================================
# BAIXAR VÍDEO DO TELEGRAM
# ============================================================

def baixar_video(file_id):
    url_info = (
        f"https://api.telegram.org/bot{TOKEN}/getFile"
        f"?file_id={file_id}"
    )

    with urllib.request.urlopen(url_info) as resposta:
        dados = json.loads(
            resposta.read().decode("utf-8")
        )

    file_path = dados["result"]["file_path"]

    url_video = (
        f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    )

    with urllib.request.urlopen(url_video) as resposta:
        video_bytes = resposta.read()

    return video_bytes


# ============================================================
# ENVIAR VÍDEO PARA O SUPABASE STORAGE
# ============================================================

def enviar_para_supabase(video_bytes, nome_arquivo):
    url = (
        f"{SUPABASE_URL}/storage/v1/object/videos/"
        f"{nome_arquivo}"
    )

    headers = {
        "Authorization": f"Bearer {SUPABASE_SECRET_KEY}",
        "apikey": SUPABASE_SECRET_KEY,
        "Content-Type": "video/mp4",
        "x-upsert": "true"
    }

    resposta = requests.post(
        url,
        data=video_bytes,
        headers=headers,
        timeout=120
    )

    resposta.raise_for_status()

    return resposta.text


# ============================================================
# CRIAR ITEM NA FILA
# ============================================================

def criar_fila(chat_id, file_id, shopee_link):
    url = f"{SUPABASE_URL}/rest/v1/videos_lote"

    dados = {
        "chat_id": chat_id,
        "telegram_file_id": file_id,
        "shopee_link": shopee_link,
        "status": "recebido"
    }

    headers = {
        "Authorization": f"Bearer {SUPABASE_SECRET_KEY}",
        "apikey": SUPABASE_SECRET_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    resposta = requests.post(
        url,
        json=dados,
        headers=headers,
        timeout=30
    )

    resposta.raise_for_status()

    return resposta.text


# ============================================================
# IDENTIFICAR LINK DA SHOPEE
# ============================================================

def encontrar_link_shopee(texto):
    """
    Procura links da Shopee dentro de um texto.

    Aceita, por exemplo:

    https://s.shopee.com.br/xxxxx
    https://shopee.com.br/xxxxx
    https://www.shopee.com.br/xxxxx
    https://shopee.com/xxxxx
    https://www.shopee.com/xxxxx
    """

    if not texto:
        return ""

    padrao = re.compile(
        r'https?://(?:www\.)?'
        r'(?:s\.shopee\.com\.br|shopee\.com\.br|shopee\.com)'
        r'[^\s<>"\']+',
        re.IGNORECASE
    )

    resultado = padrao.search(texto)

    if not resultado:
        return ""

    link = resultado.group(0)

    # Remove pontuação que possa ter sido colocada
    # imediatamente depois do link na legenda.
    link = link.rstrip(".,;:!?)]}")

    return link


# ============================================================
# TESTE DO WEBHOOK
# ============================================================

@app.get("/api/webhook")
async def teste():
    return {
        "ok": True,
        "message": "Webhook ativo"
    }


# ============================================================
# WEBHOOK PRINCIPAL
# ============================================================

@app.post("/api/webhook")
async def webhook(request: Request):

    etapa = "recebendo a mensagem"
    chat_id = None

    try:
        update = await request.json()

        mensagem = update.get("message", {})

        chat = mensagem.get("chat", {})
        chat_id = chat.get("id")

        if not chat_id:
            return {"ok": True}

        # ====================================================
        # RECEBE VÍDEO
        # ====================================================

        video = mensagem.get("video")

        if video:

            legenda = mensagem.get("caption", "")

            file_id = video["file_id"]

            etapa = "baixando o vídeo do Telegram"

            video_bytes = baixar_video(file_id)

            nome_storage = f"{file_id}.mp4"

            etapa = "enviando o vídeo para o Supabase"

            enviar_para_supabase(
                video_bytes,
                nome_storage
            )

            # =================================================
            # ENCONTRAR LINK DA SHOPEE
            # =================================================

            shopee_link = encontrar_link_shopee(
                legenda
            )

            # =================================================
            # CRIAR FILA
            # =================================================

            etapa = "criando a fila no Supabase"

            criar_fila(
                chat_id,
                file_id,
                shopee_link
            )

            # =================================================
            # RESPOSTA PARA O TELEGRAM
            # =================================================

            etapa = "enviando confirmação"

            if shopee_link:

                resposta = (
                    "🎬 Vídeo recebido!\n\n"
                    "🔗 Link da Shopee identificado.\n"
                    "☁️ Vídeo enviado para o Supabase.\n"
                    "📋 Vídeo colocado na fila.\n"
                    "💻 Pronto para o computador pegar."
                )

            else:

                resposta = (
                    "🎬 Vídeo recebido!\n\n"
                    "☁️ Vídeo enviado para o Supabase.\n"
                    "⚠️ Não encontrei o link da Shopee.\n\n"
                    "Envie o link junto com o vídeo."
                )

            enviar_mensagem(
                chat_id,
                resposta
            )

            return {"ok": True}

        # ====================================================
        # RECEBE TEXTO
        # ====================================================

        texto = mensagem.get("text", "")

        if encontrar_link_shopee(texto):

            resposta = (
                "🛒 Link da Shopee recebido!\n\n"
                "🎬 Agora envie o vídeo correspondente."
            )

        elif texto == "/start":

            resposta = (
                "👋 Olá!\n\n"
                "🎬 Envie um vídeo com o link da Shopee "
                "na legenda."
            )

        else:

            resposta = (
                "📦 Envie um vídeo com o link da Shopee "
                "na legenda."
            )

        enviar_mensagem(
            chat_id,
            resposta
        )

        return {"ok": True}

    # ========================================================
    # ERRO
    # ========================================================

    except Exception as erro:

        try:

            if chat_id:

                enviar_mensagem(
                    chat_id,
                    (
                        "❌ Ocorreu um erro.\n\n"
                        f"📍 Etapa: {etapa}\n"
                        f"⚠️ Erro: {erro}"
                    )
                )

        except Exception:
            pass

        return {"ok": True}