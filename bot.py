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

CAPITALE = 10000
RISK_PER_TRADE = 0.02
RISK_REWARD = 2.0
MIN_CONFIDENCE = 70

# Tickers base + scanner anomali
BASE_TICKERS = [
    "AAPL", "MSFT", "NVDA", "TSLA", "META",
    "AMD", "AMZN", "GOOGL"
]

SCAN_TICKERS = [
    "PLTR", "SOFI", "DKNG", "AFRM", "COIN",
    "RIVN", "LCID", "SHOP", "SNAP", "ROKU"
]

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

def position_size(entry, stop):
    rischio = abs(entry - stop)
    if rischio == 0:
        return 0
    return int((CAPITALE * RISK_PER_TRADE) / rischio)

# ======================
# TREND MERCATO
# ======================
def market_trend():
    df = yf.download("^GSPC", period="6mo", interval="1d", progress=False)
    if df.empty:
        return "NEUTRAL"

    df = clean_df(df)
    close = df["Close"]
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()

    if last(ma50) > last(ma200):
        return "UP"
    elif last(ma50) < last(ma200):
        return "DOWN"
    return "NEUTRAL"

# ======================
# SCANNER MOVIMENTI ANOMALI
# ======================
def anomalous_move(ticker):
    df = yf.download(ticker, period="2mo", interval="1d", progress=False)
    if df.empty or len(df) < 25:
        return None

    df = clean_df(df)
    close = df["Close"]
    volume = df["Volume"]

    price = last(close)
    if price < 3:
        return None

    vol_ratio = last(volume) / volume.rolling(20).mean().iloc[-1]
    daily_move = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100

    if vol_ratio >= 2.5 and abs(daily_move) >= 4:
        direction = "BUY" if daily_move > 0 else "SELL"
        return {
            "ticker": ticker,
            "direction": direction,
            "vol_ratio": round(vol_ratio, 2),
            "move": round(daily_move, 2)
        }

    return None

# ======================
# ANALISI OPERATIVA
# ======================
def analyze_trade(ticker, trend):
    df = yf.download(ticker, period="4mo", interval="1d", progress=False)
    if df.empty or len(df) < 60:
        return None

    df = clean_df(df)
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    rsi_val = last(rsi(close))
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    atr = (high - low).rolling(14).mean()

    signal = None
    confidence = 0

    if trend == "UP" and last(close) > last(ma20) > last(ma50) and rsi_val < 50:
        signal = "BUY"
        confidence = 75 + (50 - rsi_val)
    elif trend == "DOWN" and last(close) < last(ma20) < last(ma50) and rsi_val > 50:
        signal = "SELL"
        confidence = 75 + (rsi_val - 50)

    if not signal or confidence < MIN_CONFIDENCE:
        return None

    entry = last(close)
    atr_val = last(atr)

    if signal == "BUY":
        stop = entry - atr_val
        target = entry + atr_val * RISK_REWARD
    else:
        stop = entry + atr_val
        target = entry - atr_val * RISK_REWARD

    lots = position_size(entry, stop)

    return {
        "ticker": ticker,
        "signal": signal,
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "lots": lots,
        "confidence": round(min(confidence, 95), 1)
    }

# ======================
# MAIN
# ======================
async def main():
    trend = market_trend()
    signals = []

    # Analisi titoli principali
    for t in BASE_TICKERS:
        r = analyze_trade(t, trend)
        if r:
            signals.append(r)

    # Scanner anomalie
    for t in SCAN_TICKERS:
        anomaly = anomalous_move(t)
        if anomaly:
            r = analyze_trade(t, trend)
            if r:
                r["note"] = f"⚡ Volume {anomaly['vol_ratio']}x | Move {anomaly['move']}%"
                signals.append(r)

    if not signals:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"📭 Nessuna opportunità forte oggi\nTrend: {trend}"
        )
        return

    msg = f"🔥 SEGNALI AD ALTO EDGE\nTrend mercato: {trend}\n\n"

    for s in sorted(signals, key=lambda x: x["confidence"], reverse=True):
        msg += (
            f"📌 {s['ticker']} — {s['signal']}\n"
            f"Entry: {s['entry']}\n"
            f"Stop: {s['stop']}\n"
            f"Target: {s['target']}\n"
            f"Lotti: {s['lots']}\n"
            f"Confidenza: {s['confidence']}%\n"
        )
        if "note" in s:
            msg += f"{s['note']}\n"
        msg += "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
