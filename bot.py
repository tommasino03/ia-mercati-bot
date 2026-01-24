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
MIN_CONFIDENCE = 65  # %

CAPITALE_INIZIALE = 1000.0
capital = CAPITALE_INIZIALE

LOG_FILE = "trades_log.csv"

# ======================
# UTILS
# ======================
def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def last(x):
    if isinstance(x, pd.Series):
        return float(x.iloc[-1])
    return float(x)

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

    rsi_val = last(rsi(close))
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    atr_val = last((high - low).rolling(14).mean())

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
# SIMULAZIONE PAPER TRADING
# ======================
def paper_trade(trade):
    global capital
    # calcolo pnl semplice (chiude sempre a target per test)
    if trade["signal"] == "BUY":
        pnl = trade["target"] - trade["entry"]
    else:
        pnl = trade["entry"] - trade["target"]

    qty = capital / trade["entry"]  # tutto il capitale in un titolo
    profit = pnl * qty
    capital += profit

    # log su CSV
    row = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ticker": trade["ticker"],
        "signal": trade["signal"],
        "entry": trade["entry"],
        "target": trade["target"],
        "stop": trade["stop"],
        "profit": round(profit, 2),
        "capital": round(capital, 2)
    }

    df_log = pd.DataFrame([row])
    if os.path.exists(LOG_FILE):
        df_log.to_csv(LOG_FILE, mode="a", header=False, index=False)
    else:
        df_log.to_csv(LOG_FILE, mode="w", header=True, index=False)

    return row

# ======================
# MAIN
# ======================
async def main():
    trend = market_trend()
    results = []

    for t in TICKERS:
        trade = analyze(t, trend)
        if trade:
            row = paper_trade(trade)
            results.append(row)

    if not results:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"📭 Nessun trade valido oggi\nCapitale: {round(capital,2)}€\nTrend mercato: {trend}"
        )
        return

    msg = f"🚀 PAPER TRADING - SEGNALI OPERATIVI\nTrend mercato: {trend}\nCapitale attuale: {round(capital,2)}€\n\n"
    for r in sorted(results, key=lambda x: x["profit"], reverse=True):
        msg += (
            f"📌 {r['ticker']} — {r['signal']}\n"
            f"Entry: {r['entry']}\n"
            f"Target: {r['target']}\n"
            f"Stop: {r['stop']}\n"
            f"Profit simulato: {r['profit']}\n\n"
        )

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
