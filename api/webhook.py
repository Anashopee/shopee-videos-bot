import os
import json
import urllib.request
from pathlib import Path
from fastapi import FastAPI, Request

from worker.video_processor import process_video

app = FastAPI()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]


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
    url_info = (
        f"https://api.telegram.org/bot{TOKEN}/getFile"
        f"?file_id={file_id}"
    )

    with urllib.request.urlopen(url_info) as resposta:
        dados = json.loads(resposta.read().decode("utf-8"))

    file_path = dados["result"]["file_path"]

    url_video = (
        f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    )

    destino = f"/tmp/{nome_arquivo}"

    urllib.request.urlretrieve(url_video, destino)

    return destino


@app.get("/api/webhook")
async def teste():
    return {
        "ok": True,
        "message": "Webhook ativo"
    }


@app.post("/api/webhook")
async def webhook(request: Request):
    try:
        update = await request.json()
    except Exception:
        return {"ok": True}

    mensagem = update.get("message", {})
    chat = mensagem.get("chat", {})
    chat_id = chat.get("id")

    if not chat_id:
        return {"ok": True}

    video = mensagem.get("video")

    if video:
        legenda = mensagem.get("caption", "")

        try:
            file_id = video["file_id"]

            nome_arquivo = f"telegram_{file_id}.mp4"

            caminho_video = baixar_video(
                file_id,
                nome_arquivo
            )

            # Processa o vídeo automaticamente
            nome_processado = f"processado_{file_id}.mp4"

            caminho_processado = f"/tmp/{nome_processado}"

            process_video(
                caminho_video,
                caminho_processado
            )

            if "shopee.com.br" in legenda or "shopee.com" in legenda:
                resposta = (
                    "🎬 Vídeo recebido!\n\n"
                    "🔗 Link da Shopee identificado.\n"
                    "⬇️ Vídeo baixado.\n"
                    "⚙️ Vídeo processado automaticamente.\n"
                    "✅ Pronto para o próximo passo!"
                )
            else:
                resposta = (
                    "🎬 Vídeo recebido!\n\n"
                    "⬇️ Vídeo baixado.\n"
                    "⚙️ Vídeo processado automaticamente.\n"
                    "⚠️ Não encontrei o link da Shopee.\n\n"
                    "Envie o link junto com o vídeo."
                )

        except Exception as erro:
            resposta = (
                "❌ Ocorreu um erro ao processar o vídeo.\n\n"
                f"Erro: {erro}"
            )

        enviar_mensagem(chat_id, resposta)
        return {"ok": True}

    texto = mensagem.get("text", "")

    if "shopee.com.br" in texto or "shopee.com" in texto:
        resposta = (
            "🛒 Link da Shopee recebido!\n\n"
            "🎬 Agora envie o vídeo correspondente."
        )

    elif texto == "/start":
        resposta = (
            "👋 Olá!\n\n"
            "🎬 Envie seus vídeos com o link da Shopee "
            "na legenda."
        )

    else:
        resposta = (
            "📦 Envie um vídeo com o link da Shopee "
            "na legenda."
        )

    enviar_mensagem(chat_id, resposta)

    return {"ok": True}