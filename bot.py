import os
import asyncio
import yfinance as yf
import pandas as pd
from datetime import datetime
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ASSETS = [
    "AAPL", "AMZN", "GOOGL", "META", "TSLA", "NVDA",
    "JPM", "BAC", "V", "MA", "ADBE", "CSCO", "WMT",
    "SPY", "QQQ"
]

def calculate_trend(close: pd.Series):
    close = close.dropna()
    if len(close) < 60:
        return "⚠️ neutro", "⚠️ neutro", "⚠️ neutro"

    last = float(close.iloc[-1])
    ema20 = float(close.ewm(span=20).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])

    breve = "✅ COMPRA" if last > ema20 else "⚠️ neutro"
    medio = "✅ COMPRA" if ema20 > ema50 else "⚠️ neutro"
    lungo = "✅ INVESTI" if last > ema50 else "⚠️ neutro"

    return breve, medio, lungo

def analyze(symbol):
    df = yf.download(symbol, period="6mo", interval="1d", progress=False)
    close = df["Close"]

    breve, medio, lungo = calculate_trend(close)

    return f"""
📌 {symbol}
Breve: {breve}
Medio: {medio}
Lungo: {lungo}
"""

def build_report():
    date = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI – {date}\n\n"

    for s in ASSETS:
        report += analyze(s)

    report += "\n🧠 Mercato: POSITIVO\nStrategia: COMPRARE SUI RITRACCIAMENTI\nRischio: MEDIO"
    return report

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError("BOT_TOKEN o CHAT_ID mancanti")

    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=build_report())

if __name__ == "__main__":
    asyncio.run(main())
