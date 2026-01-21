import os
import asyncio
import yfinance as yf
import pandas as pd
from telegram import Bot

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti")

bot = Bot(token=TELEGRAM_TOKEN)

LARGE_CAPS = ["AAPL", "MSFT", "AMZN", "GOOGL", "TSLA"]
SMALL_CAPS = ["PLTR", "FUBO", "ROKU", "SNAP", "ZM"]

RSI_BUY = 35
RSI_SELL = 65
VOL_SPIKE = 1.8

# =========================
# UTILS
# =========================
def clean_df(df):
    """Rende il DataFrame compatibile anche con colonne MultiIndex"""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def last(series):
    return float(series.values[-1])

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# =========================
# TREND MERCATO
# =========================
def trend_mercato():
    df = yf.download("^GSPC", period="3mo", interval="1d", progress=False)
    if df.empty or len(df) < 50:
        return "NEUTRAL"

    df = clean_df(df)
    close = df["Close"].astype(float)
    ma50 = close.rolling(50).mean()

    return "UP" if last(close) > last(ma50) else "DOWN"

# =========================
# ANALISI TITOLO
# =========================
def analizza_titolo(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    if df.empty or len(df) < 30:
        return None

    df = clean_df(df)

    close = df["Close"].astype(float)
    volume = df["Volume"].astype(float)

    ma20 = close.rolling(20).mean()
    rsi_val = last(rsi(close))
    vol_last = last(volume)
    vol_mean = float(volume.rolling(20).mean().iloc[-1])

    volume_spike = vol_last > vol_mean * VOL_SPIKE

    signal = None
    score = 0

    if last(close) > last(ma20) and rsi_val < RSI_BUY and volume_spike:
        signal = "BUY"
        score = round((RSI_BUY - rsi_val) + (vol_last / vol_mean), 2)

    elif last(close) < last(ma20) and rsi_val > RSI_SELL and volume_spike:
        signal = "SELL"
        score = round((rsi_val - RSI_SELL) + (vol_last / vol_mean), 2)

    if signal:
        return {
            "ticker": ticker,
            "signal": signal,
            "rsi": round(rsi_val, 2),
            "vol_ratio": round(vol_last / vol_mean, 2),
            "score": score
        }

    return None

# =========================
# MAIN
# =========================
async def main():
    trend = trend_mercato()
    print(f"\n📊 Trend mercato: {trend}\n")

    segnali = []

    for t in LARGE_CAPS + SMALL_CAPS:
        res = analizza_titolo(t)
        if res:
            segnali.append(res)

    if not segnali:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text="📭 Nessun segnale operativo oggi"
        )
        return

    segnali.sort(key=lambda x: x["score"], reverse=True)

    msg = f"🔥 SEGNALI OPERATIVI ({trend})\n\n"
    for s in segnali:
        msg += (
            f"{s['ticker']} | {s['signal']}\n"
            f"RSI: {s['rsi']} | Vol x{s['vol_ratio']} | Score: {s['score']}\n\n"
        )

    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
