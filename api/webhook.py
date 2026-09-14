import os
import json
import urllib.request
from pathlib import Path
from fastapi import FastAPI, Request

app = FastAPI()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

INPUT_DIR = Path("input")
INPUT_DIR.mkdir(parents=True, exist_ok=True)


def enviar_mensagem(chat_id, texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    dados = json.dumps({
        "chat_id": chat_id,
        "text": texto
    }).encode("utf-8")

    requisicao = urllib.request.Request(
        url,
        data=dados,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    urllib.request.urlopen(requisicao)


def baixar_video(file_id, nome_arquivo):
    # Descobre onde o Telegram armazenou o vídeo
    url_info = (
        f"https://api.telegram.org/bot{TOKEN}/getFile"
        f"?file_id={file_id}"
    )

    with urllib.request.urlopen(url_info) as resposta:
        dados = json.loads(resposta.read().decode("utf-8"))

    file_path = dados["result"]["file_path"]

    # Baixa o vídeo
    url_video = (
        f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    )

    destino = INPUT_DIR / nome_arquivo

    urllib.request.urlretrieve(url_video, destino)

    return str(destino)


@app.post("/api/webhook")
async def webhook(request: Request):
    try:
        update = await request.json()
    except Exception:
        return {"ok": True, "message": "Webhook ativo"}

    mensagem = update.get("message", {})
    chat = mensagem.get("chat", {})
    chat_id = chat.get("id")

    if not chat_id:
        return {"ok": True}

    # Recebe vídeo
    video = mensagem.get("video")

    if video:
        legenda = mensagem.get("caption", "")

        try:
            file_id = video["file_id"]

            nome_arquivo = f"telegram_{file_id}.mp4"

            caminho = baixar_video(
                file_id,
                nome_arquivo
            )

            if "shopee.com.br" in legenda or "shopee.com" in legenda:
                resposta = (
                    "🎬 Vídeo recebido!\n\n"
                    "🔗 Link da Shopee identificado.\n"
                    "⬇️ Vídeo baixado com sucesso.\n"
                    "✅ Pronto para o processamento."
                )
            else:
                resposta = (
                    "🎬 Vídeo recebido!\n\n"
                    "⬇️ Vídeo baixado com sucesso.\n"
                    "⚠️ Não encontrei o link da Shopee na legenda.\n\n"
                    "Envie o link junto com o vídeo."
                )

        except Exception as erro:
            resposta = (
                "❌ Não consegui baixar o vídeo.\n\n"
                f"Erro: {erro}"
            )

        enviar_mensagem(chat_id, resposta)
        return {"ok": True}

    # Recebe mensagem de texto
    texto = mensagem.get("text", "")

    if "shopee.com.br" in texto or "shopee.com" in texto:
        resposta = (
            "🛒 Link da Shopee recebido!\n\n"
            "🎬 Agora envie o vídeo correspondente."
        )

    elif texto == "/start":
        resposta = (
            "👋 Olá!\n\n"
            "🎬 Envie o vídeo com o link da Shopee "
            "na legenda."
        )

    else:
        resposta = (
            "📦 Envie um vídeo com o link da Shopee "
            "na legenda."
        )

    enviar_mensagem(chat_id, resposta)

    return {"ok": True}