import os
import asyncio
from telegram import Bot

async def main():
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    chat_id = os.environ.get("CHAT_ID", "").strip()

    print("TOKEN:", "OK" if token else "MANCANTE")
    print("CHAT_ID:", chat_id if chat_id else "MANCANTE")

    bot = Bot(token=token)

    await bot.send_message(
        chat_id=chat_id,
        text="✅ TEST TECNICO: se leggi questo, Telegram funziona."
    )

    print("MESSAGGIO INVIATO")

if __name__ == "__main__":
    asyncio.run(main())
