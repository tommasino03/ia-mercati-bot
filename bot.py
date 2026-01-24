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

CAPITALE_INIZIALE = 1000  # capitale per paper trading
RISK_REWARD = 2.0
MIN_CONFIDENCE = 60  # %
TOP_N = 10  # quanti top movers considerare

# ======================
# UTILS
# ======================
def last(series):
    return float(series.iloc[-1])

def pct_change(series, period=1):
    return (series / series.shift(period) - 1) * 100

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

# ======================
# TOP MOVERS
# ======================
def get_top_movers():
    # Lista ampia di titoli da monitorare
    tickers = [
        "AAPL","MSFT","AMZN","GOOGL","TSLA",
        "NVDA","META","AMD","PLTR","ROKU",
        "ALIBABA","CRM","INTC","UBER","LYFT",
        "SNAP","SPOT","PINS","SHOP","BABA"
    ]
    movers = []
    for t in tickers:
        df = yf.download(t, period="5d", interval="1d", progress=False)
        if df.empty:
            continue
        df = clean_df(df)
        df["daily_change"] = pct_change(df["Close"])
        movers.append((t, last(df["daily_change"])))
    movers = sorted(movers, key=lambda x: abs(x[1]), reverse=True)
    top = [t for t, change in movers[:TOP_N]]
    return top

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
    elif last(ma50) < last(ma200]:
        return "DOWN"
    return "NEUTRAL"

# ======================
# ANALISI TITOLO
# ======================
def analyze(ticker, trend):
    df = yf.download(ticker, period="1mo", interval="1h", progress=False)
    if df.empty or len(df) < 20:
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

    signal = None
    confidence = 0

    # ======================
    # LOGICA TRADE SEMPLIFICATA E PIÙ REATTIVA
    # ======================
    if trend == "UP" and last(close) > last(ma20):
        if rsi_val < 50:
            signal = "BUY"
            confidence = 60 + (50 - rsi_val)
    elif trend == "DOWN" and last(close) < last(ma20):
        if rsi_val > 50:
            signal = "SELL"
            confidence = 60 + (rsi_val - 50)

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
# MAIN PAPER TRADING
# ======================
async def main():
    trend = market_trend()
    top_tickers = get_top_movers()
    results = []

    for t in top_tickers:
        res = analyze(t, trend)
        if res:
            results.append(res)

    if not results:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"📭 Nessun trade valido oggi\nTrend mercato: {trend}\nCapitale: {CAPITALE_INIZIALE}$"
        )
        return

    msg = f"🚀 SEGNALI PAPER TRADING\nTrend mercato: {trend}\nCapitale: {CAPITALE_INIZIALE}$\n\n"
    for r in sorted(results, key=lambda x: x["confidence"], reverse=True):
        msg += (
            f"📌 {r['ticker']} — {r['signal']}\n"
            f"Entry: {r['entry']}\n"
            f"Stop: {r['stop']}\n"
            f"Target: {r['target']}\n"
            f"Confidenza: {r['confidence']}%\n\n"
        )

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
