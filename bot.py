import yfinance as yf
import pandas as pd
import asyncio
from telegram import Bot

TOKEN = "INSERISCI_TOKEN"
CHAT_ID = "INSERISCI_CHAT_ID"

SOGLIA_MOVE = 2.5  # % movimento anomalo
bot = Bot(token=TOKEN)

TICKERS = ["PLTR", "SOFI", "RIVN", "LCID", "UPST"]

# =====================
# ANALISI MOVIMENTO
# =====================
def intraday_move(ticker):
    df = yf.download(ticker, period="1d", interval="5m")
    if df.empty:
        return None

    open_price = df["Open"].iloc[0]
    last_price = df["Close"].iloc[-1]
    move = ((last_price - open_price) / open_price) * 100
    return round(move, 2)

# =====================
# SEGNALE OPERATIVO
# =====================
def segnale_operativo(ticker):
    df = yf.download(ticker, period="1d", interval="5m")
    if df.empty:
        return "NO DATA"

    last = df["Close"].iloc[-1]
    high = df["High"].max()
    low = df["Low"].min()
    move = intraday_move(ticker)

    if move is None:
        return "NO DATA"

    # BUY
    if last >= high * 0.995 and move >= SOGLIA_MOVE:
        return "BUY 🚀 breakout + momentum"

    # SELL
    if last <= low * 1.005 and move <= -SOGLIA_MOVE:
        return "SELL 🔻 breakdown"

    return "HOLD ⏸"

# =====================
# BOT TELEGRAM
# =====================
async def main():
    messaggio = "📊 **SEGNALI DI MERCATO**\n\n"

    for ticker in TICKERS:
        move = intraday_move(ticker)
        segnale = segnale_operativo(ticker)

        if move is not None:
            messaggio += (
                f"📈 {ticker}\n"
                f"Movimento: {move}%\n"
                f"Segnale: {segnale}\n\n"
            )

    await bot.send_message(chat_id=CHAT_ID, text=messaggio)

if __name__ == "__main__":
    asyncio.run(main())
