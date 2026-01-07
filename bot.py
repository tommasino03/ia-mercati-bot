import os
from telegram import Bot

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    bot = Bot(token=token)

    bot.send_message(
        chat_id=chat_id,
        text="✅ TEST OK: se leggi questo messaggio, il bot può scrivere"
    )

if __name__ == "__main__":
    main()
