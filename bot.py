import os
import yfinance as yf
from telegram import Bot

def get_env(name):
    value = os.getenv(name)
    if value:
        return value.strip().replace('"', '').replace("'", "")
    return None

def main():
    TELEGRAM_TOKEN = get_env("TELEGRAM_TOKEN")
    CHAT_ID = get_env("CHAT_ID")

    bot = Bot(token=TELEGRAM_TOKEN)

    data = yf.download("AAPL", period="5d", progress=False)
    last_price = round(float(data["Close"].iloc[-1]), 2)

    bot.send_message(
        chat_id=CHAT_ID,
        text=f"📈 AAPL ultimo prezzo: {last_price}$"
    )

if __name__ == "__main__":
    main()
