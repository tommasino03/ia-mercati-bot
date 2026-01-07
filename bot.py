import os
import yfinance as yf
from telegram import Bot

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token or not chat_id:
        raise ValueError("TELEGRAM_TOKEN o CHAT_ID mancanti")

    bot = Bot(token=token)

    data = yf.download("AAPL", period="5d", progress=False)

    if data.empty:
        bot.send_message(chat_id=chat_id, text="❌ Nessun dato disponibile per AAPL")
        return

    price = round(float(data["Close"].iloc[-1]), 2)

    bot.send_message(
        chat_id=chat_id,
        text=f"📈 Prezzo attuale AAPL: ${price}"
    )

if __name__ == "__main__":
    main()
