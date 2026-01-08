import os
import asyncio
from telegram import Bot


async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token or not chat_id:
        raise ValueError("Token o Chat ID mancanti")

    bot = Bot(token=token)

    message = (
        "✅ Bot operativo!\n\n"
        "📊 Sistema stabile\n"
        "🤖 Telegram OK\n"
        "🚀 Pronto per il prossimo step"
    )

    await bot.send_message(chat_id=chat_id, text=message)


if __name__ == "__main__":
    asyncio.run(main())
