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

    if chat_id:
        enviar_mensagem(
            chat_id,
            "✅ Recebi! Seu bot da Shopee está funcionando."
        )

    return {"ok": True}
