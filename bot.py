import os
import yfinance as yf
import pandas as pd
from telegram import Bot
from datetime import datetime

def main():
    # Prendi token e chat ID dai secrets
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")

    if not TELEGRAM_TOKEN or not CHAT_ID:
        raise ValueError("Token o Chat ID mancanti")

    bot = Bot(token=TELEGRAM_TOKEN)

    # Lista ticker da monitorare
    tickers = ["AAPL", "GOOGL", "META", "TSLA", "JPM", "BAC"]

    report = f"📊 REPORT IA MERCATI – {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"

    for ticker in tickers:
        try:
            data = yf.Ticker(ticker).history(period="5d")
            if data.empty:
                report += f"📌 {ticker} - Nessun dato disponibile\n"
                continue
            last_price = round(float(data["Close"].iloc[-1]), 2)
            trend = "✅ COMPRA" if last_price > data["Close"].mean() else "⚠️ NEUTRO"
            report += f"📌 {ticker}\nPrezzo ultimo: {last_price}\nTrend breve: {trend}\n\n"
        except Exception as e:
            report += f"📌 {ticker} - Errore: {e}\n\n"

    # Invia messaggio Telegram
    bot.send_message(chat_id=CHAT_ID, text=report)

if __name__ == "__main__":
    main()
