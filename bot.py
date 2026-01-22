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
    raise ValueError("❌ Token Telegram mancanti")

bot = Bot(token=TOKEN)

TICKERS = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "TSLA",
    "NVDA", "META", "AMD", "PLTR", "ROKU"
]

RISK_REWARD = 2.0
MIN_CONFIDENCE = 65  # %
INTRADAY_VOLUME_MULTIPLIER = 1.5

# ======================
# UTILS
# ======================
def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def last(x):
    return float(x.iloc[-1])

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ======================
# TREND MERCATO
# ======================
def market_trend():
    df = yf.download("^GSPC", period="6mo", interval="1d", progress=False)
    if df.empty:
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
# ANALISI TITOLO GIORNALIERA
# ======================
def analyze(ticker, trend):
    df = yf.download(ticker, period="4mo", interval="1d", progress=False)
    if df.empty or len(df) < 60:
        return None

    df = clean_df(df)
    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)

    rsi_val = last(rsi(close))
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    atr_val = last((high - low).rolling(14).mean())

    signal = None
    confidence = 0

    if trend == "UP" and last(close) > last(ma20) > last(ma50) and rsi_val < 45:
        signal = "BUY"
        confidence = 70 + (45 - rsi_val)
    elif trend == "DOWN" and last(close) < last(ma20) < last(ma50) and rsi_val > 55:
        signal = "SELL"
        confidence = 70 + (rsi_val - 55)

    if not signal or confidence < MIN_CONFIDENCE:
        return None

    entry = last(close)
    if signal == "BUY":
        stop = entry - atr_val
        target = entry + atr_val * RISK_REWARD
    else:
        stop = entry + atr_val
        target = entry - atr_val * RISK_REWARD

    edge = abs(target - entry) / atr_val if atr_val != 0 else 0

    return {
        "ticker": ticker,
        "signal": signal,
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "confidence": round(min(confidence, 95), 1),
        "edge": round(edge, 2)
    }

# ======================
# ALERT INTRADAY
# ======================
def intraday_alert(ticker):
    df = yf.download(ticker, period="7d", interval="1h", progress=False)
    if df.empty or len(df) < 20:
        return None

    df = clean_df(df)
    close = df["Close"].astype(float)
    volume = df["Volume"].astype(float)

    ma20 = close.rolling(20).mean()
    vol_mean = volume.rolling(20).mean()

    last_price = last(close)
    last_ma20 = last(ma20)
    last_vol = last(volume)
    last_vol_mean = last(vol_mean)

    alerts = []
    if last_price > last_ma20:
        alerts.append("prezzo sopra MA20 intraday 🔼")
    elif last_price < last_ma20:
        alerts.append("prezzo sotto MA20 intraday 🔽")

    if last_vol > last_vol_mean * INTRADAY_VOLUME_MULTIPLIER:
        alerts.append("volume anomalo 🔊")

    if alerts:
        return f"{ticker}: " + ", ".join(alerts)
    return None

# ======================
# MAIN
# ======================
async def main():
    trend = market_trend()
    results = []

    # segnali giornalieri con ranking
    for t in TICKERS:
        res = analyze(t, trend)
        if res:
            results.append(res)

    # ordina per edge e confidenza
    results_sorted = sorted(results, key=lambda x: (x["edge"], x["confidence"]), reverse=True)

    msg = f"🚀 SEGNALI OPERATIVI HYPER-POWER\nTrend mercato: {trend}\n\n"

    if results_sorted:
        for r in results_sorted:
            msg += (
                f"📌 {r['ticker']} — {r['signal']}\n"
                f"Entry: {r['entry']}\n"
                f"Stop: {r['stop']}\n"
                f"Target: {r['target']}\n"
                f"Confidenza: {r['confidence']}%\n"
                f"Edge operativo: {r['edge']}\n\n"
            )
    else:
        msg += "📭 Nessun trade valido oggi\n"

    # alert intraday
    for t in TICKERS:
        alert = intraday_alert(t)
        if alert:
            msg += f"⏱ {alert}\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
