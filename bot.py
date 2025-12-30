import os
import asyncio
import yfinance as yf
import pandas as pd
from telegram import Bot

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ASSETS = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD"
}

def download_data(symbol):
    df = yf.download(symbol, period="7d", interval="1d", progress=False)
    if df.empty or "Close" not in df:
        return None
    return df["Close"]

def calculate_trend(prices: pd.Series):
    prices = prices.dropna()

    if len(prices) < 3:
        return "⚠️ dati insufficienti"

    last = float(prices.iloc[-1])
    mean_short = float(prices.iloc[-3:].mean())
    mean_long = float(prices.mean())

    if last > mean_short > mean_long:
        return "✅ trend rialzista"
    elif last < mean_short < mean_long:
        return "❌ trend ribassista"
    else:
        return "⚠️ laterale"

def build_report():
    lines = ["📊 *Report Mercati Giornaliero*\n"]

    for name, symbol in ASSETS.items():
        prices = download_data(symbol)

        if prices is None:
            lines.append(f"• {name}: ❌ dati non disponibili")
            continue

        trend = calculate_trend(prices)
        price = float(prices.iloc[-1])

        lines.append(
            f"• *{name}*\n"
            f"  Prezzo: {price:.2f}\n"
            f"  Segnale: {trend}\n"
        )

    return "\n".join(lines)

async def main():
    bot = Bot(token=TOKEN)
    report = build_report()
    await bot.send_message(
        chat_id=CHAT_ID,
        text=report,
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    asyncio.run(main())
