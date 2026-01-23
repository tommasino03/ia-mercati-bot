import os
import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
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
MIN_CONFIDENCE = 65
MIN_EDGE = 2.0
LOG_FILE = "trades_log.csv"

# ======================
# UTILS SICURI
# ======================
def clean_df(df):
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
# ANALISI TITOLO
# ======================
def analyze(ticker, trend):
    df = yf.download(ticker, period="4mo", interval="1d", progress=False)
    if df.empty or len(df) < 60:
        return None

    df = clean_df(df)

    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    volume = df["Volume"].astype(float)

    rsi_val = last(rsi(close))
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    atr = (high - low).rolling(14).mean()
    atr_val = last(atr)

    signal = None
    confidence = 0

    if trend == "UP":
        if last(close) > last(ma20) > last(ma50) and rsi_val < 45:
            signal = "BUY"
            confidence = 70 + (45 - rsi_val)

    elif trend == "DOWN":
        if last(close) < last(ma20) < last(ma50) and rsi_val > 55:
            signal = "SELL"
            confidence = 70 + (rsi_val - 55)

    if not signal or confidence < MIN_CONFIDENCE:
        return None

    entry = last(close)

    if signal == "BUY":
        stop = entry - atr_val
        target = entry + atr_val * RISK_REWARD
        edge = (target - entry) / (entry - stop)
    else:
        stop = entry + atr_val
        target = entry - atr_val * RISK_REWARD
        edge = (entry - target) / (stop - entry)

    if edge < MIN_EDGE:
        return None

    return {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ticker": ticker,
        "signal": signal,
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "confidence": round(min(confidence, 95), 1),
        "edge": round(edge, 2)
    }

# ======================
# LOG TRADE
# ======================
def log_trade(trade):
    df = pd.DataFrame([trade])
    if not os.path.exists(LOG_FILE):
        df.to_csv(LOG_FILE, index=False)
    else:
        df.to_csv(LOG_FILE, mode="a", header=False, index=False)

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
            log_trade(r)

    if not results:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"📭 Nessun trade valido oggi\nTrend mercato: {trend}"
        )
        return

    msg = f"🚀 SEGNALI OPERATIVI\nTrend mercato: {trend}\n\n"

    for r in sorted(results, key=lambda x: x["confidence"], reverse=True):
        msg += (
            f"📌 {r['ticker']} — {r['signal']}\n"
            f"Entry: {r['entry']}\n"
            f"Stop: {r['stop']}\n"
            f"Target: {r['target']}\n"
            f"Confidenza: {r['confidence']}%\n"
            f"Edge: {r['edge']}\n\n"
        )

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
