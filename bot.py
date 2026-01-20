import yfinance as yf
import asyncio
import os
import pandas as pd
from telegram import Bot

# =========================
# ENV
# =========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("❌ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti")

bot = Bot(token=TOKEN)

# =========================
# CONFIG
# =========================
TICKERS = ["PLTR", "SOFI", "RIVN", "LCID", "UPST", "AFRM", "HOOD"]
MIN_EDGE = 50

# =========================
# INDICATORI
# =========================
def rsi(close, periodi=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(periodi).mean()
    loss = -delta.where(delta < 0, 0.0).rolling(periodi).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def atr(df, periodi=14):
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - df["Close"].shift()).abs(),
        (df["Low"] - df["Close"].shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(periodi).mean()

# =========================
# EDGE (STEP 8)
# =========================
def calcola_edge(ticker):
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if df.empty or len(df) < 60:
        return None

    close = df["Close"]
    profitto = (float(close.iloc[-1]) - float(close.iloc[0])) / float(close.iloc[0]) * 100
    winrate = 55  # proxy stabile
    drawdown = ((close.cummax() - close) / close.cummax()).max() * 100

    edge = (profitto * 1.5) + winrate - (drawdown * 2)

    return round(edge, 2)

# =========================
# SEGNALE OPERATIVO
# =========================
def segnale_operativo(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    if df.empty or len(df) < 30:
        return None

    close = df["Close"]
    prezzo = float(close.iloc[-1])
    r = float(rsi(close).iloc[-1])
    ma20 = float(close.rolling(20).mean().iloc[-1])

    supporto = float(df["Low"].iloc[-10:].min())
    rischio = prezzo - supporto
    if rischio <= 0:
        return None

    stop = round(supporto, 2)
    target = round(prezzo + rischio * 2, 2)

    if 30 <= r <= 50 and prezzo > ma20:
        return ("BUY", prezzo, stop, target, r)

    if r >= 70 or prezzo < ma20:
        return ("SELL", prezzo, stop, target, r)

    return ("HOLD", prezzo, stop, target, r)

# =========================
# MAIN
# =========================
async def main():
    msg = "📡 SEGNALI OPERATIVI\n\n"

    segnali = 0

    for t in TICKERS:
        edge = calcola_edge(t)
        if not edge or edge < MIN_EDGE:
            continue

        res = segnale_operativo(t)
        if not res:
            continue

        azione, prezzo, stop, target, rsi_val = res
        segnali += 1

        msg += (
            f"🔹 {t}\n"
            f"EDGE: {edge}\n"
            f"Segnale: {azione}\n"
            f"Prezzo: {prezzo}\n"
            f"Stop: {stop}\n"
            f"Target: {target}\n"
            f"RSI: {round(rsi_val,1)}\n\n"
        )

    if segnali == 0:
        msg += "⚠️ Nessun segnale valido oggi"

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
