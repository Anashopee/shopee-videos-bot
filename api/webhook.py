import os
import json
import urllib.request
from fastapi import FastAPI, Request

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


@app.post("/api/webhook")
async def webhook(request: Request):
    update = await request.json()

    mensagem = update.get("message", {})
    chat = mensagem.get("chat", {})
    chat_id = chat.get("id")

    if not chat_id:
        return {"ok": True}

    # Verifica se recebeu um vídeo
    video = mensagem.get("video")

    if video:
        legenda = mensagem.get("caption", "")

        if "shopee.com.br" in legenda or "shopee.com" in legenda:
            resposta = (
                "🎬 Vídeo recebido!\n\n"
                "🔗 Link da Shopee identificado.\n"
                "✅ Vídeo pronto para o próximo passo."
            )
        else:
            resposta = (
                "🎬 Vídeo recebido!\n\n"
                "⚠️ Não encontrei o link da Shopee na legenda.\n"
                "Envie o vídeo com o link da Shopee na legenda."
            )

        enviar_mensagem(chat_id, resposta)
        return {"ok": True}

    # Verifica mensagens de texto
    texto = mensagem.get("text", "")

    if "shopee.com.br" in texto or "shopee.com" in texto:
        resposta = (
            "🛒 Link da Shopee recebido!\n\n"
            "🔗 Agora você pode enviar o vídeo correspondente."
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
