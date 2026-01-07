import os
import yfinance as yf
from telegram import Bot

TICKERS = ["AAPL", "MSFT", "TSLA"]

def main():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")

    # ✅ NON blocchiamo più il bot
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Secrets non disponibili: esecuzione terminata")
        return

    bot = Bot(token=TELEGRAM_TOKEN)

    lines = ["📊 Aggiornamento Mercati"]

    for ticker in TICKERS:
        try:
            data = yf.download(
                ticker,
                period="5d",
                interval="1d",
                progress=False
            )

            if data.empty:
                continue

            price = round(float(data["Close"].iloc[-1]), 2)
            lines.append(f"{ticker}: ${price}")

        except Exception:
            continue

    if len(lines) > 1:
        bot.send_message(
            chat_id=CHAT_ID,
            text="\n".join(lines)
        )

if __name__ == "__main__":
    main()
