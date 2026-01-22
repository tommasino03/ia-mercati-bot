import os
import json
import asyncio
import datetime
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

CAPITAL = 10_000
RISK_PER_TRADE = 0.01
MAX_DRAWDOWN = -0.05
RISK_REWARD = 2.0

TICKERS = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "TSLA",
    "NVDA", "META", "AMD", "PLTR", "ROKU"
]

LOG_FILE = "trade_log.json"

# ======================
# UTILS
# ======================
def last(s):
    return float(s.iloc[-1])

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def load_log():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        return json.load(f)

def save_log(data):
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ======================
# RISK CONTROL
# ======================
def drawdown_exceeded():
    log = load_log()
    if not log:
        return False

    pnl = sum(t["pnl"] for t in log if "pnl" in t)
    return pnl / CAPITAL <= MAX_DRAWDOWN

# ======================
# ANALISI
# ======================
def analyze(ticker):
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if df.empty or len(df) < 80:
        return None

    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    atr = (high - low).rolling(14).mean()
    rsi_val = last(rsi(close))

    if not (last(close) > last(ma20) > last(ma50)):
        return None
    if rsi_val > 50:
        return None

    entry = last(close)
    atr_val = last(atr)

    size = int((CAPITAL * RISK_PER_TRADE) / atr_val)
    if size <= 0:
        return None

    return {
        "ticker": ticker,
        "entry": round(entry, 2),
        "stop": round(entry - atr_val, 2),
        "target": round(entry + atr_val * RISK_REWARD, 2),
        "size": size,
        "confidence": round(70 + (45 - rsi_val), 1)
    }

# ======================
# MAIN
# ======================
async def main():
    if drawdown_exceeded():
        await bot.send_message(
            chat_id=CHAT_ID,
            text="🛑 Trading BLOCCATO\nDrawdown massimo raggiunto"
        )
        return

    trades = []
    for t in TICKERS:
        r = analyze(t)
        if r:
            trades.append(r)

    if not trades:
        await bot.send_message(
            chat_id=CHAT_ID,
            text="📭 Nessun trade valido oggi"
        )
        return

    best = sorted(trades, key=lambda x: x["confidence"], reverse=True)[0]

    log = load_log()
    log.append({
        "date": str(datetime.date.today()),
        "ticker": best["ticker"],
        "entry": best["entry"],
        "stop": best["stop"],
        "target": best["target"],
        "size": best["size"],
        "confidence": best["confidence"]
    })
    save_log(log)

    msg = (
        "🏆 **TRADE SELEZIONATO**\n\n"
        f"{best['ticker']}\n"
        f"Entry: {best['entry']}\n"
        f"Stop: {best['stop']}\n"
        f"Target: {best['target']}\n"
        f"Size: {best['size']}\n"
        f"Confidenza: {best['confidence']}%\n\n"
        "⚠️ Rispetta stop e size"
    )

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
