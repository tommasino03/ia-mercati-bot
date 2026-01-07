import os
import yfinance as yf
from telegram import Bot

def main():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")

    bot = Bot(token=TELEGRAM_TOKEN)

    data = yf.download("AAPL", period="5d")
    last_price = round(float(data["Close"].iloc[-1]), 2)

    bot.send_message(
        chat_id=CHAT_ID,
        text=f"📈 AAPL ultimo prezzo: {last_price}$"
    )

if __name__ == "__main__":
    main()
