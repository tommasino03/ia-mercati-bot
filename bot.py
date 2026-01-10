import yfinance as yf
import asyncio
import os
from telegram import Bot

# =====================
# ENV
# =====================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("TOKEN o CHAT_ID mancanti")

bot = Bot(token=TOKEN)

SOGLIA_MOVE = 2.5  # %

TICKERS = ["PLTR", "SOFI", "RIVN", "LCID", "UPST"]

# =====================
# MOVIMENTO INTRADAY
# =====================
def intraday_move(ticker):
    df = yf.download(ticker, period="1d", interval="5m", progress=False)

    if df.empty:
        return None

    open_price = df["Open"].iloc[0].item()
    last_price = df["Close"].iloc[-1].item()

    move = ((last_price - open_price) / open_price) * 100
    return round(move, 2)

# =====================
# SEGNALE OPERATIVO
# =====================
def segnale_operativo(ticker):
    df = yf.download(ticker, period="1d", interval="5m", progress=False)

    if df.empty:
        return "NO DATA"

    last = df["Close"].iloc[-1].item()
    high = df["High"].max().item()
    low = df["Low"].min().item()

    move = intraday_move(ticker)
    if move is None:
        return "NO DATA"

    if last >= high * 0.995 and move >= SOGLIA_MOVE:
        return "BUY 🚀 Breakout"

    if last <= low * 1.005 and move <= -SOGLIA_MOVE:
        return "SELL 🔻 Breakdown"

    return "HOLD ⏸"

# =====================
# MAIN
# =====================
async def main():
    messaggio = "📊 SEGNALI DI MERCATO\n\n"

    for ticker in TICKERS:
        move = intraday_move(ticker)
        segnale = segnale_operativo(ticker)

        if move is not None:
            messaggio += (
                f"{ticker}\n"
                f"Movimento: {move}%\n"
                f"Segnale: {segnale}\n\n"
            )

    await bot.send_message(chat_id=CHAT_ID, text=messaggio)

if __name__ == "__main__":
    asyncio.run(main())
