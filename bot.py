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
# UTILS SICURI
# ======================
def scalar(x):
    """Restituisce SEMPRE un float sicuro"""
    if x is None:
        return None
    if isinstance(x, pd.Series):
        if x.empty:
            return None
        return float(x.dropna().iloc[-1])
    return float(x)

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
    pnl = sum(t.get("pnl", 0) for t in log)
    return pnl / CAPITAL <= MAX_DRAWDOWN

# ======================
# ANALISI TITOLO
# ======================
def analyze(ticker):
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if df.empty or len(df) < 80:
        return None

    df = df.dropna()

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    atr = (high - low).rolling(14).mean()
    rsi_series = rsi(close)

    last_close = scalar(close)
    last_ma20 = scalar(ma20)
    last_ma50 = scalar(ma50)
    last_atr = scalar(atr)
    last_rsi = scalar(rsi_series)

    if None in (last_close, last_ma20, last_ma50, last_atr, last_rsi):
        return None

    # ======================
    # LOGICA TRADING (EDGE)
    # ======================
    if not (last_close > last_ma20 > last_ma50):
        return None

    if last_rsi > 50:
        return None

    size = int((CAPITAL * RISK_PER_TRADE) / last_atr)
    if size <= 0:
        return None

    return {
        "ticker": ticker,
        "entry": round(last_close, 2),
        "stop": round(last_close - last_atr, 2),
        "target": round(last_close + last_atr * RISK_REWARD, 2),
        "size": size,
        "confidence": round(70 + (45 - last_rsi), 1)
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

    candidates = []
    for t in TICKERS:
        res = analyze(t)
        if res:
            candidates.append(res)

    if not candidates:
        await bot.send_message(
            chat_id=CHAT_ID,
            text="📭 Nessun trade valido oggi"
        )
        return

    best = sorted(candidates, key=lambda x: x["confidence"], reverse=True)[0]

    log = load_log()
    log.append({
        "date": str(datetime.date.today()),
        **best
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
        "⚠️ Rispetta SEMPRE stop e size"
    )

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
