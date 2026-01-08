from telegram import Bot
import os
import asyncio
import json
import urllib.request

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def get_price(url):
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read())
        return round(float(data["price"]), 2)

async def main():
    btc = get_price("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")

    message = f"""
📊 *Market Report*

₿ Bitcoin: {btc} $

🧠 Stato:
– Crypto monitorate
– Bot operativo
"""

    bot = Bot(token=TOKEN)
    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    asyncio.run(main())
