import yfinance as yf
import pandas as pd
import asyncio
import os
from telegram import Bot

# =====================
# ENV
# =====================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("❌ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti")

bot = Bot(token=TOKEN)

# =====================
# CONFIG
# =====================
TICKERS = ["PLTR", "SOFI", "RIVN", "LCID", "UPST"]
SOGLIA_MOVE = 2.0          # %
RSI_BUY = 30
RSI_SELL = 70
VOLUME_MULT = 2.0

# =====================
# RSI
# =====================
def calcola_rsi(series, periodi=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(periodi).mean()
    loss = -delta.where(delta < 0, 0).rolling(periodi).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# =====================
# INTRADAY MOVE
# =====================
def intraday_move(df):
    open_price = df["Open"].iloc[0].item()
    last_price = df["Close"].iloc[-1].item()
    return round(((last_price - open_price) / open_price) * 100, 2)

# =====================
# ANALISI COMPLETA
# =====================
def analizza_ticker(ticker):
    df = yf.download(
        ticker,
        period="1d",
        interval="5m",
        progress=False
    )

    if df.empty or len(df) < 20:
        return None

    move = intraday_move(df)
    rsi = round(calcola_rsi(df["Close"]), 2)

    vol_attuale = df["Volume"].iloc[-1].item()
    vol_media = df["Volume"].rolling(20).mean().iloc[-1].item()

    volume_spike = vol_attuale >= vol_media * VOLUME_MULT

    segnale = "HOLD ⏸"

    if rsi <= RSI_BUY and volume_spike:
        segnale = "🟢 BUY FORTE"

    elif rsi >= RSI_SELL and volume_spike:
        segnale = "🔴 SELL FORTE"

    return {
        "ticker": ticker,
        "move": move,
        "rsi": rsi,
        "volume_spike": volume_spike,
        "segnale": segnale
    }

# =====================
# MAIN
# =====================
async def main():
    messaggio = "📊 SEGNALI INTRADAY\n\n"

    for ticker in TICKERS:
        dati = analizza_ticker(ticker)

        if dati is None:
            continue

        messaggio += (
            f"{dati['ticker']}\n"
            f"Movimento: {dati['move']}%\n"
            f"RSI: {dati['rsi']}\n"
            f"Volume: {'🔥 ANOMALO' if dati['volume_spike'] else 'normale'}\n"
            f"Segnale: {dati['segnale']}\n\n"
        )

    await bot.send_message(chat_id=CHAT_ID, text=messaggio)

if __name__ == "__main__":
    asyncio.run(main())
