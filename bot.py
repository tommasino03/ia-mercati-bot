import os
import asyncio
from datetime import datetime

import yfinance as yf
import pandas as pd
from telegram import Bot

# === SECRETS ===
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# === ASSET ===
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

# === CORE LOGIC ===
def calculate_trend(close: pd.Series):
    if close is None or len(close) < 50:
        return "⚠️ neutro", "⚠️ neutro", "⚠️ neutro"

    close = close.dropna()

    last = close.iloc[-1].item()
    ema20 = close.ewm(span=20).mean().iloc[-1].item()
    ema50 = close.ewm(span=50).mean().iloc[-1].item()

    if len(close) >= 200:
        ema200 = close.ewm(span=200).mean().iloc[-1].item()
    else:
        ema200 = ema50

    breve = "✅ COMPRA" if last > ema20 else "⚠️ neutro"
    medio = "✅ COMPRA" if last > ema50 else "⚠️ neutro"
    lungo = "✅ INVESTI" if last > ema200 else "⚠️ neutro"

    return breve, medio, lungo


def analyze_symbol(symbol: str) -> str:
    try:
        data = yf.download(symbol, period="1y", interval="1d", progress=False)

        if data.empty or "Close" not in data:
            return ""

        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        breve, medio, lungo = calculate_trend(close)

        return (
            f"\n📌 {symbol}\n"
            f"Breve: {breve}\n"
            f"Medio: {medio}\n"
            f"Lungo: {lungo}\n"
            f"Motivo: trend breve {breve}, trend medio {medio}, trend lungo {lungo}\n"
        )

    except Exception:
        return ""


def build_report() -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI – {now}\n"

    categories = {}
    for symbol, category in ASSETS.items():
        categories.setdefault(category, []).append(symbol)

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
