import os
import asyncio
import yfinance as yf
from telegram import Bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("TELEGRAM_TOKEN o CHAT_ID mancanti nei Secrets")

ASSETS = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD"
}

def analyze(symbol: str) -> str:
    data = yf.download(symbol, period="3mo", interval="1d", progress=False)

    if data.empty:
        return "❌ dati non disponibili\n"

    close = data["Close"]
    last = float(close.iloc[-1])
    ema20 = float(close.ewm(span=20).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])

    if last > ema20 > ema50:
        signal = "✅ COMPRA"
    elif last < ema20 < ema50:
        signal = "🔴 VENDI"
    else:
        signal = "⚠️ NEUTRO"

    return (
        f"Prezzo: {last:.2f}\n"
        f"EMA20: {ema20:.2f}\n"
        f"EMA50: {ema50:.2f}\n"
        f"Segnale: {signal}\n"
    )

def build_report() -> str:
    report = "📊 *REPORT MERCATI*\n\n"
    for name, symbol in ASSETS.items():
        report += f"*{name}*\n"
        report += analyze(symbol)
        report += "\n"
    return report

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(
        chat_id=CHAT_ID,
        text=build_report(),
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    asyncio.run(main())
