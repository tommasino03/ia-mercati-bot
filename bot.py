import os
import asyncio
import yfinance as yf
import pandas as pd
from datetime import datetime
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ASSETS = {
    "AAPL": "Azioni USA",
    "AMZN": "Azioni USA",
    "GOOGL": "Azioni USA",
    "META": "Azioni USA",
    "NVDA": "Azioni USA",
    "TSLA": "Azioni USA",
    "SPY": "ETF",
    "QQQ": "ETF",
    "BTC-USD": "Crypto",
    "ETH-USD": "Crypto",
}

def calculate_trend(close: pd.Series):
    if len(close) < 50:
        return "⚠️ neutro", "⚠️ neutro", "⚠️ neutro"

    last = float(close.iloc[-1])
    ema20 = close.ewm(span=20).mean().iloc[-1]
    ema50 = close.ewm(span=50).mean().iloc[-1]
    ema200 = close.ewm(span=200).mean().iloc[-1] if len(close) >= 200 else ema50

    breve = "✅ COMPRA" if last > ema20 else "⚠️ neutro"
    medio = "✅ COMPRA" if last > ema50 else "⚠️ neutro"
    lungo = "✅ INVESTI" if last > ema200 else "⚠️ neutro"

    return breve, medio, lungo

def analyze_symbol(symbol):
    data = yf.download(symbol, period="1y", interval="1d", progress=False)
    if data.empty or "Close" not in data:
        return ""

    close = data["Close"].dropna()
    breve, medio, lungo = calculate_trend(close)

    return (
        f"\n📌 {symbol}\n"
        f"Breve: {breve}\n"
        f"Medio: {medio}\n"
        f"Lungo: {lungo}\n"
        f"Motivo: trend breve {breve}, trend medio {medio}, trend lungo {lungo}\n"
    )

def build_report():
    today = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI – {today}\n"

    categories = {}
    for s, c in ASSETS.items():
        categories.setdefault(c, []).append(s)

    for category, symbols in categories.items():
        report += f"\n--- {category} ---\n"
        for s in symbols:
            report += analyze_symbol(s)

    report += (
        "\n🧠 SITUAZIONE GENERALE:\n"
        "Mercato: POSITIVO\n"
        "Strategia consigliata: COMPRARE SUI RITRACCIAMENTI\n"
        "Rischio: MEDIO"
    )

    return report

async def main():
    if not TOKEN or not CHAT_ID:
        raise RuntimeError("BOT_TOKEN / CHAT_ID mancanti nei Secrets GitHub")

    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=build_report())

if __name__ == "__main__":
    asyncio.run(main())
