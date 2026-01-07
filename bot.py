# bot.py - test invio messaggio Telegram

import os
from telegram import Bot

def main():
    # Prende token e chat_id dai secrets/variabili d'ambiente
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("CHAT_ID")

    if not token or not chat_id:
        raise ValueError("TELEGRAM_TOKEN o CHAT_ID mancanti nei Secrets")

    bot = Bot(token=token)

    # Messaggio di test
    test_message = "✅ Il bot funziona! Messaggio di test."
    bot.send_message(chat_id=chat_id, text=test_message)
    print("Messaggio inviato correttamente!")

if __name__ == "__main__":
    main()
