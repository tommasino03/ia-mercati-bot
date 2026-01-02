import os
import asyncio
from datetime import datetime

import yfinance as yf
import pandas as pd
from telegram import Bot

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ASSETS = {
    "Azioni USA": [
        "AAPL", "AMZN", "GOOGL", "META", "TSLA", "NVDA",
        "JPM", "BAC", "V", "MA", "ADBE", "CSCO", "CMCSA", "WMT"
    ],
    "ETF": [
        "SPY", "QQQ", "VEA", "VGK", "IWV", "VTI", "EFA", "IEMG"
    ],
    "Azioni Europa": [
        "SAN.MC"
    ]
}
# ============================================


def calculate_trend(close: pd.Series):
    close = close.dropna()

    if len(close) < 60:
        return "⚠️ neutro", "⚠️ neutro", "⚠️ neutro"

    last = float(close.iloc[-1])
    ema20 = float(close.ewm(span=20).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])
    ema200 = float(close.ewm(span=200).mean().iloc[-1])

    breve = "✅ COMPRA" if last > ema20 else "⚠️ neutro"
    medio = "✅ COMPRA" if ema20 > ema50 else "⚠️ neutro"
    lungo = "✅ INVESTI" if ema50 > ema200 else "⚠️ neutro"

    return breve, medio, lungo


def analyze_symbol(symbol: str) -> str:
    data = yf.download(symbol, period="1y", interval="1d", progress=False)

    if data.empty or "Close" not in data:
        return f"📌 {symbol}\nDati non disponibili\n\n"

    close = data["Close"]
    breve, medio, lungo = calculate_trend(close)

    return (
        f"📌 {symbol}\n"
        f"Breve: {breve}\n"
        f"Medio: {medio}\n"
        f"Lungo: {lungo}\n\n"
    )


def build_report() -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    report = f"📊 REPORT IA MERCATI – {now}\n\n"

    for section, symbols in ASSETS.items():
        report += f"--- {section} ---\n"
        for s in symbols:
            report += analyze_symbol(s)

    report += (
        "🧠 SITUAZIONE GENERALE:\n"
        "Mercato: POSITIVO\n"
        "Strategia consigliata: COMPRARE SUI RITRACCIAMENTI\n"
        "Rischio: MEDIO\n"
    )

    return report


async def main():
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError("BOT_TOKEN o CHAT_ID mancanti nei secrets GitHub")

    bot = Bot(token=BOT_TOKEN)
    report = build_report()
    await bot.send_message(chat_id=CHAT_ID, text=report)


if __name__ == "__main__":
    asyncio.run(main())
