import os
from telegram import Bot

def main():
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["CHAT_ID"]

    bot = Bot(token=token)
    bot.send_message(chat_id=chat_id, text="✅ Bot attivo: messaggio di test")

if __name__ == "__main__":
    main()
