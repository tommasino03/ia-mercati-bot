import os
import asyncio
import yfinance as yf
import pandas as pd
from telegram import Bot

# Leggi token e chat id dai secrets
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("TELEGRAM_TOKEN o CHAT_ID mancanti nei Secrets")

bot = Bot(token=TELEGRAM_TOKEN)

symbols = ["AAPL", "TSLA", "MSFT"]  # esempio

def calculate_trend(close):
    # correzione FutureWarning
    last = float(close.iloc[-1])
    ema20 = float(close.ewm(span=20).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])
    if last > ema20:
        breve = "✅ COMPRA"
    else:
        breve = "⚠️ neutro"
    if ema20 > ema50:
        medio = "📈 TENDENZA RIALZISTA"
    else:
        medio = "📉 TENDENZA RIBASSISTA"
    return breve, medio

def analyze_symbol(symbol):
    data = yf.download(symbol, period="2mo", interval="1d")
    close = data['Close']
    breve, medio = calculate_trend(close)
    return f"{symbol}: {breve} | {medio}"

def build_report():
    report = ""
    for s in symbols:
        report += analyze_symbol(s) + "\n"
    return report

async def main():
    report = build_report()
    await bot.send_message(chat_id=CHAT_ID, text=report)

if __name__ == "__main__":
    asyncio.run(main())
