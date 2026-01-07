import os
import asyncio
from telegram import Bot

async def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("CHAT_ID")

    if not token or not chat_id:
        raise ValueError("TELEGRAM_TOKEN o CHAT_ID mancanti")

    bot = Bot(token=token)

    me = await bot.get_me()   # <-- FIX CRITICO
    print(f"Bot funzionante: @{me.username}")

    await bot.send_message(
        chat_id=chat_id,
        text="✅ Messaggio di test: il bot funziona!"
    )

if __name__ == "__main__":
    asyncio.run(main())
