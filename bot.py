import os
import yfinance as yf
import pandas as pd
from telegram import Bot

# Ottieni token e chat_id dai secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("TELEGRAM_TOKEN o CHAT_ID mancanti nei Secrets")

bot = Bot(token=TELEGRAM_TOKEN)

def calculate_score(df):
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    last = df["Close"].iloc[-1]
    ema20 = df["EMA20"].iloc[-1]
    ema50 = df["EMA50"].iloc[-1]

    if last > ema20 > ema50:
        return "BUY"
    elif last < ema20 < ema50:
        return "SELL"
    else:
        return "HOLD"

def build_alerts(assets):
    alerts = []
    for asset in assets:
        df = yf.download(asset, period="60d", interval="1d")
        score = calculate_score(df)
        alerts.append(f"{asset}: {score}")
    return alerts

def main():
    assets = ["AAPL", "TSLA", "MSFT"]  # esempio, puoi modificare
    alerts = build_alerts(assets)
    message = "\n".join(alerts)
    bot.send_message(chat_id=CHAT_ID, text=message)

if __name__ == "__main__":
    main()
