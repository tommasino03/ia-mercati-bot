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

# ======================
# UTILS
# ======================
def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def last(x):
    arr = np.array(x)
    return float(arr[-1])

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
    atr_val = last((high - low).rolling(14).mean())
    vol_mean = volume.rolling(20).mean()
    vol_last = last(volume)
    volume_spike = vol_last > last(vol_mean) * 1.5

    signal = None
    confidence = 0

    # LOGICA TRADE
    if trend == "UP":
        if last(close) > last(ma20) > last(ma50) and rsi_val < 45:
            signal = "BUY"
            confidence = 70 + (45 - rsi_val)
    elif trend == "DOWN":
        if last(close) < last(ma20) < last(ma50) and rsi_val > 55:
            signal = "SELL"
            confidence = 70 + (rsi_val - 55)

    # Opportunità volume/spike (trade forti)
    if volume_spike and rsi_val < 40:
        signal = "BUY"
        confidence = max(confidence, 80)
    elif volume_spike and rsi_val > 60:
        signal = "SELL"
        confidence = max(confidence, 80)

    if not signal or confidence < MIN_CONFIDENCE:
        return None

    entry = last(close)
    if signal == "BUY":
        stop = entry - atr_val
        target = entry + atr_val * RISK_REWARD
    else:
        stop = entry + atr_val
        target = entry - atr_val * RISK_REWARD

    return {
        "ticker": ticker,
        "signal": signal,
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "confidence": round(min(confidence, 95), 1)
    }

# ======================
# MAIN
# ======================
async def main():
    trend = market_trend()
    results = []

    for t in TICKERS:
        res = analyze(t, trend)
        if res:
            results.append(res)

    if not results:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"📭 Nessun trade valido oggi\nTrend mercato: {trend}"
        )
        return

    # Ordina per confidenza e seleziona trade migliore
    results_sorted = sorted(results, key=lambda x: x["confidence"], reverse=True)
    best_trade = results_sorted[0]

    # Messaggio Telegram
    msg = f"🚀 TRADE MIGLIORE OGGI\nTrend mercato: {trend}\n\n"
    msg += (
        f"📌 {best_trade['ticker']} — {best_trade['signal']}\n"
        f"Entry: {best_trade['entry']}\n"
        f"Stop: {best_trade['stop']}\n"
        f"Target: {best_trade['target']}\n"
        f"Confidenza: {best_trade['confidence']}%\n\n"
    )
    msg += "📊 Ranking completo dei trade:\n"
    for r in results_sorted:
        msg += f"{r['ticker']}: {r['signal']} — Conf: {r['confidence']}%\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
