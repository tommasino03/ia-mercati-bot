import os
import yfinance as yf
import pandas as pd
from telegram import Bot

# Legge token e chat_id dai Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("TELEGRAM_TOKEN o CHAT_ID mancanti nei Secrets")

bot = Bot(token=TELEGRAM_TOKEN)

# Lista dei simboli da analizzare
symbols = ["AAPL", "TSLA", "MSFT"]

def calculate_trend(close: pd.Series):
    """
    Calcola trend breve, medio e lungo usando EMA e momentum
    """
    last = float(close.iloc[-1])
    ema20 = float(close.ewm(span=20).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])
    ema100 = float(close.ewm(span=100).mean().iloc[-1])
    
    breve = "✅ COMPRA" if last > ema20 else "⚠️ neutro"
    medio = "✅ COMPRA" if last > ema50 else "⚠️ neutro"
    lungo = "✅ COMPRA" if last > ema100 else "⚠️ neutro"
    return breve, medio, lungo

def analyze_symbol(symbol: str):
    data = yf.download(symbol, period="60d", interval="1d")
    close = data['Close']
    breve, medio, lungo = calculate_trend(close)
    report = f"{symbol} → Breve: {breve}, Medio: {medio}, Lungo: {lungo}\n"
    return report

def build_report():
    report = "📈 Report giornaliero dei simboli:\n\n"
    for s in symbols:
        report += analyze_symbol(s)
    return report

def main():
    message = build_report()
    bot.send_message(chat_id=CHAT_ID, text=message)

if __name__ == "__main__":
    main()
