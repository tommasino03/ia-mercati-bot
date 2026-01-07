import os
import yfinance as yf
from telegram import Bot

TICKERS = ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN"]

def main():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")

    if not TELEGRAM_TOKEN or not CHAT_ID:
        raise ValueError("TELEGRAM_TOKEN o CHAT_ID mancanti nei Secrets")

    bot = Bot(token=TELEGRAM_TOKEN)

    message_lines = ["📊 *Aggiornamento Mercati*\n"]

    for ticker in TICKERS:
        try:
            data = yf.download(ticker, period="5d", interval="1d", progress=False)

            if data.empty:
                continue

            last_price = round(float(data["Close"].iloc[-1]), 2)
            message_lines.append(f"• {ticker}: ${last_price}")

        except Exception:
            continue  # ignora ticker problematici, NO crash

    if len(message_lines) > 1:
        bot.send_message(
            chat_id=CHAT_ID,
            text="\n".join(message_lines),
            parse_mode="Markdown"
        )

if __name__ == "__main__":
    main()
