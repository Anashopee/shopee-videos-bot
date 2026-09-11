import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

async def receber_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "✅ Recebi sua mensagem! Seu bot está funcionando."
        )

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(filters.ALL, receber_mensagem)
    )

    print("Bot iniciado!")
    app.run_polling()

if __name__ == "__main__":
    main()
