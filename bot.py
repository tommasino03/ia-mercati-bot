import os
import asyncio
from telegram import Bot

# Legge i secrets da GitHub Actions / Replit / ambiente
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print("TOKEN:", "OK" if TOKEN else "MANCANTE")
print("CHAT_ID:", "OK" if CHAT_ID else "MANCANTE")

async def main():
    if not TOKEN or not CHAT_ID:
        raise ValueError("❌ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti")

    bot = Bot(token=TOKEN)

    await bot.send_message(
        chat_id=int(CHAT_ID),
        text="🚀 Bot avviato correttamente e funzionante!"
    )

if __name__ == "__main__":
    asyncio.run(main())
