import os
import asyncio
import pandas as pd
import yfinance as yf
from telegram import Bot

# Prendi token e chat id dai secrets
TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise RuntimeError("Secrets BOT_TOKEN o CHAT_ID mancanti!")

# Lista dei simboli da monitorare
symbols = ["AAPL","AMZN","GOOGL","META","TSLA","NVDA"]

def calculate_trend(close):
    """
    Calcola il trend breve, medio e lungo.
    """
    last = float(close.iloc[-1])
    ema20 = float(close.ewm(span=20).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])
    
    breve = "✅ COMPRA" if last > ema20 else "⚠️ neutro"
    medio = "✅ COMPRA" if ema20 > ema50 else "⚠️ neutro"
    lungo = "✅ INVESTI" if last > ema50 else "⚠️ neutro"
    
    return breve, medio, lungo

def analyze_symbol(symbol):
    data = yf.download(symbol, period="3mo", interval="1d")
    close = data["Close"]
    breve, medio, lungo = calculate_trend(close)
    return f"📌 {symbol}\nBreve: {breve}\nMedio: {medio}\nLungo: {lungo}\n"

def build_report():
    report = "📊 REPORT IA MERCATI\n\n"
    for s in symbols:
        report += analyze_symbol(s) + "\n"
    report += "🧠 SITUAZIONE GENERALE:\nMercato: POSITIVO\nStrategia consigliata: COMPRARE SUI RITRACCIAMENTI\nRischio: MEDIO"
    return report

async def main():
    bot = Bot(token=TOKEN)
    report = build_report()
    await bot.send_message(chat_id=CHAT_ID, text=report)

if __name__ == "__main__":
    asyncio.run(main())
