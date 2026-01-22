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
    raise ValueError("❌ Variabili Telegram mancanti")

bot = Bot(token=TOKEN)

TICKERS = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "TSLA",
    "NVDA", "META", "AMD", "PLTR", "ROKU"
]

CAPITAL = 10_000
RISK_PER_TRADE = 0.01
RISK_REWARD = 2.0

MIN_CONFIDENCE = 65
MIN_PROBABILITY = 55
MIN_SCORE = 90

# ======================
# UTILS
# ======================
def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

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

# ======================
# FILTRO MERCATO
# ======================
def market_filter():
    df = yf.download("^GSPC", period="6mo", interval="1d", progress=False)
    if df.empty or len(df) < 50:
        return False, "Dati mercato insufficienti"

    df = clean_df(df)
    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)

    atr = (high - low).rolling(14).mean()
    vol = last(atr) / last(close) * 100

    if vol < 0.6:
        return False, "Mercato piatto"
    if vol > 3.5:
        return False, "Mercato troppo volatile"

    return True, "OK"

# ======================
# PROBABILITÀ STORICA
# ======================
def historical_probability(close, atr):
    wins, total = 0, 0

    for i in range(40, len(close) - 5):
        entry = close.iloc[i]
        atr_val = atr.iloc[i]
        if atr_val <= 0 or np.isnan(atr_val):
            continue

        future = close.iloc[i+1:i+6]
        if future.max() >= entry + atr_val * RISK_REWARD:
            wins += 1
        total += 1

    return round((wins / total) * 100, 1) if total else 0

# ======================
# ANALISI
# ======================
def analyze(ticker):
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

    if not (last(close) > last(ma20) > last(ma50)):
        return None

    if rsi_val > 50:
        return None

    confidence = 70 + (45 - rsi_val)
    if confidence < MIN_CONFIDENCE:
        return None

    probability = historical_probability(close, atr)
    if probability < MIN_PROBABILITY:
        return None

    entry = last(close)
    atr_val = last(atr)

    risk_amount = CAPITAL * RISK_PER_TRADE
    size = int(risk_amount / atr_val)
    if size <= 0:
        return None

    stop = entry - atr_val
    target = entry + atr_val * RISK_REWARD

    rr = (target - entry) / (entry - stop)
    rsi_factor = (50 - rsi_val) / 10

    score = round(probability * rr * rsi_factor, 1)

    if score < MIN_SCORE:
        return None

    return {
        "ticker": ticker,
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "size": size,
        "probability": probability,
        "score": score
    }

# ======================
# MAIN
# ======================
async def main():
    ok, reason = market_filter()

    if not ok:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"🛑 NESSUN TRADE OGGI\nMotivo: {reason}"
        )
        return

    candidates = []

    for t in TICKERS:
        r = analyze(t)
        if r:
            candidates.append(r)

    if not candidates:
        await bot.send_message(
            chat_id=CHAT_ID,
            text="📭 Nessun trade con vantaggio statistico oggi"
        )
        return

    best = sorted(candidates, key=lambda x: x["score"], reverse=True)[0]

    msg = (
        "🏆 **TRADE MIGLIORE DEL GIORNO**\n\n"
        f"📌 {best['ticker']}\n"
        f"Entry: {best['entry']}\n"
        f"Stop: {best['stop']}\n"
        f"Target: {best['target']}\n"
        f"Size: {best['size']} azioni\n"
        f"Probabilità: {best['probability']}%\n"
        f"Score: {best['score']}\n\n"
        "👉 **UN SOLO TRADE. IL MIGLIORE.**"
    )

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
