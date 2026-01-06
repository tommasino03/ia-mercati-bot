# bot.py
import os
import asyncio
import pandas as pd
import yfinance as yf
from telegram import Bot
from dotenv import load_dotenv

# --- Carica i secrets sia da GitHub Actions sia da .env locale ---
load_dotenv()  # legge .env se esiste
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("TELEGRAM_TOKEN o CHAT_ID mancanti nei Secrets o .env")

# --- Funzioni di analisi ---
def calculate_trend(close: pd.Series):
    """
    Calcola trend breve, medio e lungo periodo
    """
    if len(close) < 50:  # sicurezza
        return "N/A", "N/A", "N/A"

    last = float(close.iloc[-1])
    ema20 = float(close.ewm(span=20).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])
    momentum = (last / float(close.iloc[-20]) - 1) * 100

    breve = "✅ COMPRA" if last > ema20 else "⚠️ neutro"
    medio = "✅ COMPRA" if ema20 > ema50 else "⚠️ neutro"
    lungo = "✅ COMPRA" if momentum > 0 else "⚠️ neutro"

    return breve, medio, lungo

def analyze_symbol(symbol: str):
    """
    Recupera dati e calcola trend
    """
    data = yf.download(symbol, period="2mo", interval="1d", progress=False)
    if data.empty:
        return f"{symbol}: dati non disponibili\n"
    close = data['Close']
    breve, medio, lungo = calculate_trend(close)
    report = f"{symbol}:\n  Breve: {breve}\n  Medio: {medio}\n  Lungo: {lungo}\n\n"
    return report

def build_report():
    """
    Costruisce il report completo per tutti i simboli
    """
    symbols = ["AAPL", "MSFT", "TSLA", "GOOGL"]  # esempio, cambia con i tuoi simboli
    report = ""
    for s in symbols:
        report += analyze_symbol(s)
    return report

# --- Main ---
async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    report = build_report()
    await bot.send_message(chat_id=CHAT_ID, text=report)

if __name__ == "__main__":
    asyncio.run(main())
