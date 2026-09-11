import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler

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


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        tamanho = int(self.headers.get("content-length", 0))
        corpo = self.rfile.read(tamanho)

        try:
            update = json.loads(corpo)

            mensagem = update.get("message", {})
            chat = mensagem.get("chat", {})
            chat_id = chat.get("id")

            if chat_id:
                enviar_mensagem(
                    chat_id,
                    "✅ Recebi! Seu bot da Shopee está funcionando."
                )

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

        except Exception as erro:
            print(erro)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok":false}')
