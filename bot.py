import os
from telegram import Bot

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token or not chat_id:
        raise ValueError("Token o Chat ID mancanti")

    chat_id = int(chat_id)  # 🔴 FIX CRITICO

    bot = Bot(token=token)

    bot.send_message(
        chat_id=chat_id,
        text="✅ Messaggio di test: il bot funziona correttamente."
    )

    print("Messaggio inviato con successo")

if __name__ == "__main__":
    main()
