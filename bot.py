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
MIN_CONFIDENCE = 60
INITIAL_CAPITAL = 1000  # capitale virtuale iniziale

# ======================
# UTILS
# ======================
def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def last(x):
    return float(np.array(x)[-1])

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()

# ======================
# TREND MERCATO
# ======================
def market_trend():
    df = yf.download("^GSPC", period="6mo", interval="1d", progress=False)
    if df.empty:
        return "NEUTRAL"
    df = clean_df(df)
    close = df['Close'].astype(float)
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
    df = yf.download(ticker, period="2mo", interval="60m", progress=False)
    if df.empty or len(df) < 30:
        return None
    df = clean_df(df)
    close = df['Close'].astype(float)
    high = df['High'].astype(float)
    low = df['Low'].astype(float)
    volume = df['Volume'].astype(float)

    rsi_val = last(rsi(close))
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    atr_val = last(atr(df))
    vol_mean = volume.rolling(20).mean()
    vol_last = last(volume)
    volume_spike = vol_last > last(vol_mean) * 1.5

    signal = None
    confidence = 0

    if trend == "UP":
        if last(close) > last(ma20) > last(ma50) and rsi_val < 50 and volume_spike:
            signal = "BUY"
            confidence = 65 + (50 - rsi_val)
    elif trend == "DOWN":
        if last(close) < last(ma20) < last(ma50) and rsi_val > 50 and volume_spike:
            signal = "SELL"
            confidence = 65 + (rsi_val - 50)

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
# PAPER TRADING
# ======================
capital = INITIAL_CAPITAL
positions = {}

def execute_trade(trade):
    global capital, positions
    ticker = trade["ticker"]
    signal = trade["signal"]
    entry = trade["entry"]
    stop = trade["stop"]
    target = trade["target"]

    position_size = capital * 0.1  # investiamo 10% del capitale per trade
    shares = position_size / entry

    positions[ticker] = {
        "signal": signal,
        "entry": entry,
        "stop": stop,
        "target": target,
        "shares": shares
    }

async def update_positions():
    global capital, positions
    to_remove = []
    for ticker, pos in positions.items():
        df = yf.download(ticker, period="5d", interval="60m", progress=False)
        if df.empty:
            continue
        last_price = last(df['Close'].astype(float))
        if pos['signal'] == "BUY":
            if last_price <= pos['stop'] or last_price >= pos['target']:
                pnl = (last_price - pos['entry']) * pos['shares']
                capital += pnl
                to_remove.append(ticker)
        else:
            if last_price >= pos['stop'] or last_price <= pos['target']:
                pnl = (pos['entry'] - last_price) * pos['shares']
                capital += pnl
                to_remove.append(ticker)
    for t in to_remove:
        del positions[t]

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
            execute_trade(res)

    await update_positions()

    if not results and not positions:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"📭 Nessun trade valido ora\nCapitale: {round(capital,2)}$\nTrend mercato: {trend}"
        )
        return

    msg = f"🚀 PAPER TRADING\nTrend mercato: {trend}\nCapitale: {round(capital,2)}$\n\n"

    for r in sorted(results, key=lambda x: x["confidence"], reverse=True):
        msg += (
            f"📌 {r['ticker']} — {r['signal']}\n"
            f"Entry: {r['entry']}\n"
            f"Stop: {r['stop']}\n"
            f"Target: {r['target']}\n"
            f"Confidenza: {r['confidence']}%\n\n"
        )

    if positions:
        msg += "💼 POSIZIONI APERTE:\n"
        for t, p in positions.items():
            msg += (
                f"{t} — {p['signal']} — Entry: {p['entry']} — Stop: {p['stop']} — Target: {p['target']}\n"
            )

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
