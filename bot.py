import os
import asyncio
import requests
from datetime import datetime
from telegram import Bot


ALERT_PRICE = 43000  # soglia alert BTC


def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd"
    }
    response = requests.get(url, timeout=10)
    data = response.json()
    return float(data["bitcoin"]["usd"])


async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token or not chat_id:
        raise ValueError("Token o Chat ID mancanti")

    bot = Bot(token=token)

    btc_price = get_btc_price()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    message = (
        "🚨 **ALERT BITCOIN**\n\n"
        f"🕒 {now}\n"
        f"₿ Prezzo BTC: ${btc_price}\n"
        f"🎯 Soglia: ${ALERT_PRICE}\n\n"
    )

    if btc_price >= ALERT_PRICE:
        message += "✅ **BTC sopra la soglia!** 🚀"
    else:
        message += "⏳ BTC sotto la soglia"

    await bot.send_message(chat_id=chat_id, text=message)


if __name__ == "__main__":
    asyncio.run(main())
