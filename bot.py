import os
from telegram.ext import ApplicationBuilder, MessageHandler, filters

TOKEN = os.getenv("TELEGRAM_TOKEN")

async def first_message(update, context):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"✅ CHAT_ID CORRETTO TROVATO:\n{chat_id}"
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, first_message))
    app.run_polling()

if __name__ == "__main__":
    main()
