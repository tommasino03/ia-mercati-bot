import os
import asyncio
from telegram import Bot

async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token or not chat_id:
        raise ValueError("Token o Chat ID mancanti")

    bot = Bot(token=token)

    await bot.send_message(
        chat_id=int(chat_id),
        text="✅ Messaggio di test: il bot funziona davvero."
    )

    print("Messaggio inviato")

if __name__ == "__main__":
    asyncio.run(main())
