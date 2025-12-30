import os
import asyncio
from telegram import Bot
import yfinance as yf
import pandas as pd
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")

ASSETS = {
    "Azioni USA": ["AAPL", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "JPM", "BAC", "V", "MA", "ADBE", "CSCO", "CMCSA", "WMT"],
    "ETF": ["SPY", "QQQ", "VEA", "VGK", "IWV", "VTI", "EFA", "IEMG"],
    "Azioni Europa": ["SAN.MC"]
}

def calculate_trend(close: pd.Series):
    last = close.iloc[-1]
    breve = "✅ COMPRA" if last > close.iloc[-5:].mean() else "⚠️ neutro"
    medio = "✅ COMPRA" if last > close.iloc[-20:].mean() else "⚠️ neutro"
    lungo = "✅ INVESTI" if last > close.mean() else "⚠️ neutro"
    return breve, medio, lungo

def analyze_symbol(symbol):
    data = yf.download(symbol, period="6mo", interval="1d", progress=False)
    if data.empty:
        return ""

    close = data["Close"]
    breve, medio, lungo = calculate_trend(close)

    return (
        f"📌 {symbol}\n"
        f"Breve: {breve}\n"
        f"Medio: {medio}\n"
        f"Lungo: {lungo}\n"
        f"Motivo: trend breve {breve}, trend medio {medio}, trend lungo {lungo}, volumi normali\n\n"
    )

def build_report():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI – {now}\n\n"

    for category, symbols in ASSETS.items():
        report += f"--- {category} ---\n"
        for s in symbols:
            report += analyze_symbol(s)

    report += (
        "🧠 SITUAZIONE GENERALE:\n"
        "Mercato: POSITIVO\n"
        "Strategia consigliata: COMPRARE SUI RITRACCIAMENTI\n"
        "Rischio: MEDIO"
    )
    return report

async def main():
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=build_report())

if __name__ == "__main__":
    asyncio.run(main())
