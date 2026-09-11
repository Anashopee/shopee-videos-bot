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
    texto = mensagem.get("text", "")

    if chat_id:

        if "shopee.com.br" in texto or "shopee.com" in texto:
            resposta = (
                "🛒 Link da Shopee recebido!\n\n"
                "🔗 Vou preparar esse produto para o próximo passo."
            )
        else:
            resposta = (
                "👋 Olá!\n\n"
                "Envie um link de produto da Shopee "
                "para eu começar a processar."
            )

        enviar_mensagem(chat_id, resposta)

    return {"ok": True}
