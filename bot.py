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
    raise ValueError("Token Telegram mancanti")

bot = Bot(token=TOKEN)

TICKERS = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "TSLA",
    "NVDA", "META", "AMD", "PLTR", "ROKU"
]

CAPITALE_INIZIALE = 1000
RISK_REWARD = 2
MIN_CONFIDENCE = 65

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
# ANALISI TITOLO
# ======================
def analyze(ticker, trend, capitale):
    df = yf.download(ticker, period="4mo", interval="1d", progress=False)
    if df.empty or len(df) < 60:
        return None, capitale

    df = clean_df(df)

    close = df["Close"]
    open_p = df["Open"]
    high = df["High"]
    low = df["Low"]

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    rsi_val = last(rsi(close))
    atr = last((high - low).rolling(14).mean())

    daily_change = (last(close) - last(open_p)) / last(open_p) * 100
    is_mover = abs(daily_change) >= 3

    reasons = []
    signal = None
    confidence = 0

    # ===== LOGICA BUY =====
    if trend == "UP":
        if last(close) > last(ma20) > last(ma50):
            reasons.append("Prezzo sopra MA20 e MA50 (trend rialzista)")
        if rsi_val < 45:
            reasons.append(f"RSI basso ({round(rsi_val,1)}) → pullback")
        if len(reasons) >= 2:
            signal = "BUY"
            confidence = 70 + (45 - rsi_val)

    # ===== LOGICA SELL =====
    if trend == "DOWN":
        if last(close) < last(ma20) < last(ma50):
            reasons.append("Prezzo sotto MA20 e MA50 (trend ribassista)")
        if rsi_val > 55:
            reasons.append(f"RSI alto ({round(rsi_val,1)}) → eccesso")
        if len(reasons) >= 2:
            signal = "SELL"
            confidence = 70 + (rsi_val - 55)

    # ===== MOVERS =====
    if not signal and is_mover:
        signal = "BUY" if daily_change > 0 else "SELL"
        confidence = 75
        reasons.append(f"Mover giornaliero {round(daily_change,2)}%")

    if not signal or confidence < MIN_CONFIDENCE:
        return None, capitale

    entry = last(close)
    qty = max(1, int(capitale / entry))

    if signal == "BUY":
        stop = entry - atr
        target = entry + atr * RISK_REWARD
    else:
        stop = entry + atr
        target = entry - atr * RISK_REWARD

    capitale -= qty * entry

    return {
        "ticker": ticker,
        "signal": signal,
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "qty": qty,
        "confidence": round(min(confidence, 95), 1),
        "reasons": reasons
    }, capitale

# ======================
# MAIN
# ======================
async def main():
    trend = market_trend()
    capitale = CAPITALE_INIZIALE
    trades = []

    for t in TICKERS:
        res, capitale = analyze(t, trend, capitale)
        if res:
            trades.append(res)

    if not trades:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"Nessun trade oggi\nTrend: {trend}\nCapitale: {capitale}$"
        )
        return

    msg = f"📊 PAPER TRADING\nTrend mercato: {trend}\n\n"

    for t in trades:
        msg += (
            f"📌 {t['ticker']} — {t['signal']}\n"
            f"Entry: {t['entry']}$ | Stop: {t['stop']}$ | Target: {t['target']}$\n"
            f"Qty: {t['qty']} | Confidenza: {t['confidence']}%\n"
            f"Perché:\n"
        )
        for r in t["reasons"]:
            msg += f"• {r}\n"
        msg += "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
