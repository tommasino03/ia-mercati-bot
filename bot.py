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
MIN_CONFIDENCE = 65
MIN_PROBABILITY = 55   # 🔥 soglia reale di convenienza

# ======================
# UTILS
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
# BACKTEST PROBABILITÀ
# ======================
def historical_probability(close, atr, signal):
    wins = 0
    total = 0

    for i in range(30, len(close) - 5):
        entry = close.iloc[i]
        atr_val = atr.iloc[i]
        if atr_val == 0 or np.isnan(atr_val):
            continue

        if signal == "BUY":
            stop = entry - atr_val
            target = entry + atr_val * RISK_REWARD
            future = close.iloc[i+1:i+6]
            if future.max() >= target:
                wins += 1
            elif future.min() <= stop:
                pass
            else:
                continue
        else:
            stop = entry + atr_val
            target = entry - atr_val * RISK_REWARD
            future = close.iloc[i+1:i+6]
            if future.min() <= target:
                wins += 1
            elif future.max() >= stop:
                pass
            else:
                continue

        total += 1

    if total == 0:
        return 0

    return round((wins / total) * 100, 1)

# ======================
# ANALISI TITOLO
# ======================
def analyze(ticker, trend):
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if df.empty or len(df) < 80:
        return None

    df = clean_df(df)
    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    atr = (high - low).rolling(14).mean()
    rsi_val = last(rsi(close))

    signal = None
    confidence = 0

    if trend == "UP" and last(close) > last(ma20) > last(ma50) and rsi_val < 45:
        signal = "BUY"
        confidence = 70 + (45 - rsi_val)

    if trend == "DOWN" and last(close) < last(ma20) < last(ma50) and rsi_val > 55:
        signal = "SELL"
        confidence = 70 + (rsi_val - 55)

    if not signal or confidence < MIN_CONFIDENCE:
        return None

    probability = historical_probability(close, atr, signal)
    if probability < MIN_PROBABILITY:
        return None

    entry = last(close)
    atr_val = last(atr)

    if signal == "BUY":
        stop = entry - atr_val
        target = entry + atr_val * RISK_REWARD
    else:
        stop = entry + atr_val
        target = entry - atr_val * RISK_REWARD

    expected_value = probability/100 * RISK_REWARD - (1 - probability/100)

    return {
        "ticker": ticker,
        "signal": signal,
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "confidence": round(confidence, 1),
        "probability": probability,
        "ev": round(expected_value, 2)
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
            text=f"📭 Nessuna operazione con vantaggio reale oggi\nTrend: {trend}"
        )
        return

    results = sorted(results, key=lambda x: x["ev"], reverse=True)

    msg = f"💰 TRADE CON VANTAGGIO STATISTICO\nTrend mercato: {trend}\n\n"

    for r in results:
        msg += (
            f"📌 {r['ticker']} — {r['signal']}\n"
            f"Entry: {r['entry']}\n"
            f"Stop: {r['stop']}\n"
            f"Target: {r['target']}\n"
            f"Probabilità storica: {r['probability']}%\n"
            f"Valore atteso (EV): {r['ev']}\n\n"
        )

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
