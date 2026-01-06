import asyncio
import os
import yfinance as yf
import pandas as pd
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise RuntimeError("BOT_TOKEN o CHAT_ID mancanti")

SYMBOLS = ["AAPL", "MSFT", "GOOGL"]

def analyze_symbol(symbol: str) -> str:
    df = yf.download(symbol, period="3mo", interval="1d", progress=False)

    if df.empty or len(df) < 50:
        return f"{symbol}: dati insufficienti\n\n"

    close = df["Close"]

    price = float(close.iloc[-1])
    ema20 = float(close.ewm(span=20).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])
    momentum = (price / float(close.iloc[-20]) - 1) * 100

    breve = "✅ COMPRA" if price > ema20 else "⚠️ neutro"
    medio = "✅ COMPRA" if ema20 > ema50 else "⚠️ neutro"
    lungo = "✅ COMPRA" if momentum > 0 else "⚠️ neutro"

    return (
        f"{symbol}\n"
        f"• Trend breve: {breve}\n"
        f"• Trend medio: {medio}\n"
        f"• Trend lungo: {lungo}\n\n"
    )

def build_report() -> str:
    report = "📊 Report Mercati\n\n"
    for symbol in SYMBOLS:
        report += analyze_symbol(symbol)
    return report

async def main():
    bot = Bot(token=TOKEN)
    report = build_report()
    await bot.send_message(chat_id=CHAT_ID, text=report)

if __name__ == "__main__":
    asyncio.run(main())
