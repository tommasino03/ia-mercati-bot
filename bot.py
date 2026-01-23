import os
import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import Bot
from datetime import datetime

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

CAPITALE = 10000  # capitale simulato
RISK_PER_TRADE = 0.02  # rischio 2% per trade
RISK_REWARD = 2.0
MIN_CONFIDENCE = 65  # %

# ======================
# UTILS
# ======================
def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def last_val(series):
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

    if last_val(ma50) > last_val(ma200):
        return "UP"
    elif last_val(ma50) < last_val(ma200):
        return "DOWN"
    return "NEUTRAL"

# ======================
# CALCOLO LOTTO E STOP/TRAILING
# ======================
def calc_position_size(entry, stop):
    rischio_per_azione = abs(entry - stop)
    if rischio_per_azione == 0:
        return 0
    lotti = int((CAPITALE * RISK_PER_TRADE) / rischio_per_azione)
    return max(lotti, 1)

def trailing_stop(entry, stop, current, signal):
    if signal == "BUY":
        return max(stop, current - (entry - stop))
    else:
        return min(stop, current + (stop - entry))

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

    rsi_val = last_val(rsi(close))
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    atr_val = last_val((high - low).rolling(14).mean())

    signal = None
    confidence = 0

    # ======================
    # LOGICA TRADE
    # ======================
    if trend == "UP":
        if last_val(close) > last_val(ma20) > last_val(ma50) and rsi_val < 45:
            signal = "BUY"
            confidence = 70 + (45 - rsi_val)
    elif trend == "DOWN":
        if last_val(close) < last_val(ma20) < last_val(ma50) and rsi_val > 55:
            signal = "SELL"
            confidence = 70 + (rsi_val - 55)

    if not signal or confidence < MIN_CONFIDENCE:
        return None

    entry = last_val(close)
    if signal == "BUY":
        stop = entry - atr_val
        target = entry + atr_val * RISK_REWARD
    else:
        stop = entry + atr_val
        target = entry - atr_val * RISK_REWARD

    lotti = calc_position_size(entry, stop)

    return {
        "ticker": ticker,
        "signal": signal,
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "confidence": round(min(confidence, 95), 1),
        "lots": lotti
    }

# ======================
# REPORT
# ======================
def build_message(results, trend):
    if not results:
        return f"📭 Nessun trade valido oggi\nTrend mercato: {trend}"

    msg = f"🚀 SEGNALI OPERATIVI\nTrend mercato: {trend}\n\n"
    for r in sorted(results, key=lambda x: x["confidence"], reverse=True):
        msg += (
            f"📌 {r['ticker']} — {r['signal']}\n"
            f"Entry: {r['entry']}\n"
            f"Stop: {r['stop']}\n"
            f"Target: {r['target']}\n"
            f"Lotti consigliati: {r['lots']}\n"
            f"Confidenza: {r['confidence']}%\n\n"
        )
    return msg

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

    msg = build_message(results, trend)
    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
