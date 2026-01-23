import os
import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import Bot

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("Token Telegram mancanti")

bot = Bot(token=TOKEN)

TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","META",
    "TSLA","AMD","GOOGL","PLTR","COIN"
]

RISK_REWARD = 2.5
MIN_CONFIDENCE = 70

# ======================
# UTILS SICURI
# ======================
def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def last(series):
    return float(series.iloc[-1])

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ======================
# TREND MERCATO (SP500)
# ======================
def market_trend():
    df = yf.download("^GSPC", period="6mo", interval="1d", progress=False)
    if df.empty or len(df) < 200:
        return "NEUTRAL"

    df = clean_df(df)
    close = df["Close"].astype(float)
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()

    if last(ma50) > last(ma200):
        return "UP"
    elif last(ma50) < last(ma200):
        return "DOWN"
    return "NEUTRAL"

# ======================
# ANALISI TITOLO
# ======================
def analyze(ticker, trend):
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if df.empty or len(df) < 60:
        return None

    df = clean_df(df)

    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    volume = df["Volume"].astype(float)

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    vol_mean = volume.rolling(20).mean()

    rsi_val = last(rsi(close))
    atr = (high - low).rolling(14).mean()
    atr_val = last(atr)

    last_close = last(close)
    last_ma20 = last(ma20)
    last_ma50 = last(ma50)
    last_vol = last(volume)
    avg_vol = last(vol_mean)

    # ======================
    # FILTRI DI QUALITÀ
    # ======================
    confidence = 0
    signal = None

    if trend == "UP":
        if last_close > last_ma50 and last_ma20 > last_ma50 and 40 < rsi_val < 60:
            signal = "BUY"
            confidence += 40
    elif trend == "DOWN":
        if last_close < last_ma50 and last_ma20 < last_ma50 and 40 < rsi_val < 60:
            signal = "SELL"
            confidence += 40
    else:
        return None

    # Volume = soldi veri
    if last_vol > avg_vol * 1.2:
        confidence += 20
    else:
        return None

    # Momentum
    if abs(last_close - last_ma20) > atr_val * 0.3:
        confidence += 15

    if confidence < MIN_CONFIDENCE:
        return None

    # ======================
    # STOP & TARGET INTELLIGENTI
    # ======================
    if signal == "BUY":
        stop = last_close - atr_val * 1.1
        target = last_close + atr_val * RISK_REWARD
    else:
        stop = last_close + atr_val * 1.1
        target = last_close - atr_val * RISK_REWARD

    return {
        "ticker": ticker,
        "signal": signal,
        "entry": round(last_close, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "confidence": confidence,
        "rsi": round(rsi_val, 1)
    }

# ======================
# MAIN
# ======================
async def main():
    trend = market_trend()
    results = []

    for t in TICKERS:
        r = analyze(t, trend)
        if r:
            results.append(r)

    if not results:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"📭 Nessun trade valido oggi\nTrend mercato: {trend}"
        )
        return

    msg = f"💰 SEGNALI AD ALTA PROBABILITÀ\nTrend mercato: {trend}\n\n"

    for r in sorted(results, key=lambda x: x["confidence"], reverse=True):
        msg += (
            f"📌 {r['ticker']} — {r['signal']}\n"
            f"Entry: {r['entry']}\n"
            f"Stop: {r['stop']}\n"
            f"Target: {r['target']}\n"
            f"Confidenza: {r['confidence']}%\n"
            f"RSI: {r['rsi']}\n\n"
        )

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
