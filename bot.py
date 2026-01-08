import os
from telegram import Bot

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token or not chat_id:
        raise ValueError("Token o Chat ID mancanti")

    bot = Bot(token=token)

    message = (
        "📊 REPORT IA MERCATI\n\n"
        "✅ Bot attivo\n"
        "📈 Mercati monitorati correttamente\n"
        "🕘 Invio di test riuscito\n\n"
        "Se leggi questo messaggio, il bot FUNZIONA."
    )

    bot.send_message(chat_id=chat_id, text=message)

if __name__ == "__main__":
    main()
