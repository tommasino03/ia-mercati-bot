import os
import asyncio
from datetime import datetime
from telegram import Bot
import yfinance as yf

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SOGLIA_MOVE = 2.0  # %
TIMEFRAME = "1h"

ASSETS = {
    "BTC": "BTC-USD",
    "PLTR": "PLTR",
    "NIO": "NIO",
    "COIN": "COIN",
    "RIVN": "RIVN",
    "SOFI": "SOFI"
}

def segnale_operativo(ticker):
    df = yf.download(
        ticker,
        period="1d",
        interval=TIMEFRAME,
        progress=False
    )

    if df is None or df.empty or len(df) < 3:
        return None

    open_day = df["Open"].iloc[0]
    last = df["Close"].iloc[-1]
    high = df["High"].max()
    low = df["Low"].min()

    move = (last / open_day - 1) * 100

    # BUY
    if last >= high and move >= SOGLIA_MOVE:
        return {
            "signal": "BUY 🚀",
            "move": round(move, 2),
            "reason": "Breakout + momentum"
        }

    # SELL
    if last <= low and move <= -SOGLIA_MOVE:
        return {
            "signal": "SELL 🔻",
            "move": round(move, 2),
            "reason": "Breakdown + perdita momentum"
        }

    return None

async def main():
    if not TOKEN or not CHAT_ID:
        raise ValueError("Token o Chat ID mancanti")

    bot = Bot(token=TOKEN)
    alert = False
    msg = f"🤖 SEGNALI OPERATIVI – {datetime.now().strftime('%H:%M')}\n\n"

    for nome, ticker in ASSETS.items():
        sig = segnale_operativo(ticker)
        if sig:
            alert = True
            msg += (
                f"{nome} → {sig['signal']}\n"
                f"Motivo: {sig['reason']}\n"
                f"Movimento: {sig['move']}%\n"
                f"Timeframe: INTRADAY\n\n"
            )

    if alert:
        await bot.send_message(chat_id=int(CHAT_ID), text=msg)
    else:
        print("Nessun segnale operativo")

if __name__ == "__main__":
    asyncio.run(main())
