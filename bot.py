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
    raise ValueError("Token Telegram mancanti")

bot = Bot(token=TOKEN)

CAPITALE_INIZIALE = 1000
RISK_PER_TRADE = 0.02
RISK_REWARD = 2.0
MIN_CONFIDENCE = 65

TICKERS = [
    "AAPL","MSFT","NVDA","AMD","META","AMZN","TSLA",
    "PLTR","COIN","RIVN","SOFI","AFRM","SHOP","UBER",
    "SNAP","PYPL","ROKU","MARA","RIOT"
]

# ======================
# UTILS
# ======================
def safe_last(x):
    try:
        if isinstance(x, pd.DataFrame):
            x = x.iloc[:,0]
        if isinstance(x, pd.Series):
            x = x.dropna()
            if len(x) == 0:
                return None
            return float(x.iloc[-1])
        return float(x)
    except:
        return None

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def atr(df, period=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1)
    return tr.max(axis=1).rolling(period).mean()

# ======================
# TREND MERCATO
# ======================
def market_trend():
    df = yf.download("^GSPC", period="1y", interval="1d", progress=False)
    if df.empty or len(df) < 60:
        return "NEUTRAL"
    close = df["Close"]
    ma50 = safe_last(close.rolling(50).mean())
    ma200 = safe_last(close.rolling(200).mean())
    if ma50 is None or ma200 is None:
        return "NEUTRAL"
    return "UP" if ma50 > ma200 else "DOWN"

# ======================
# TOP MOVERS
# ======================
def top_movers():
    movers = []
    for t in TICKERS:
        df = yf.download(t, period="2d", interval="1d", progress=False)
        if df.empty or len(df) < 2:
            continue
        try:
            close_prev = float(df["Close"].iloc[-2])
            close_now = float(df["Close"].iloc[-1])
        except:
            continue
        change = ((close_now - close_prev) / close_prev) * 100
        movers.append((t, change))
    movers.sort(key=lambda x: abs(x[1]), reverse=True)
    return movers[:5]

# ======================
# ANALISI TITOLO
# ======================
def analyze_ticker(ticker, trend, capitale):
    df = yf.download(ticker, period="4mo", interval="1d", progress=False)
    if df.empty or len(df) < 60:
        return None
    df = df.dropna()
    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    volume = df["Volume"].astype(float)

    rsi_val = safe_last(rsi(close))
    ma20 = safe_last(close.rolling(20).mean())
    ma50 = safe_last(close.rolling(50).mean())
    atr_val = safe_last(atr(df))

    if None in [rsi_val, ma20, ma50, atr_val] or atr_val <= 0:
        return None

    signal = None
    confidence = 0
    last_close = safe_last(close)

    # LOGICA BUY
    if trend == "UP":
        if last_close > ma20 > ma50 and rsi_val < 45:
            signal = "BUY"
            confidence = 70 + (45 - rsi_val)
    # LOGICA SELL
    elif trend == "DOWN":
        if last_close < ma20 < ma50 and rsi_val > 55:
            signal = "SELL"
            confidence = 70 + (rsi_val - 55)

    if not signal or confidence < MIN_CONFIDENCE:
        return None

    entry = last_close
    stop = entry - atr_val if signal == "BUY" else entry + atr_val
    target = entry + atr_val * RISK_REWARD if signal == "BUY" else entry - atr_val * RISK_REWARD

    # Calcolo dimensione posizione
    risk = capitale * RISK_PER_TRADE
    size = max(1, int(risk / abs(entry - stop)))

    return {
        "ticker": ticker,
        "signal": signal,
        "entry": round(entry,2),
        "stop": round(stop,2),
        "target": round(target,2),
        "size": size,
        "confidence": round(min(confidence,95),1),
        "reason": f"Trend {trend} | RSI {round(rsi_val,1)} | ATR {round(atr_val,2)}"
    }

# ======================
# MAIN LOOP LIMITATO
# ======================
async def main():
    trend = market_trend()
    capitale = CAPITALE_INIZIALE
    risultati = []

    for _ in range(5):  # 5 cicli, GitHub Actions friendly
        movers = top_movers()
        for t,_ in movers:
            trade = analyze_ticker(t, trend, capitale)
            if trade and trade not in risultati:
                risultati.append(trade)

        if risultati:
            msg = f"🚀 NUOVI TRADE (Paper Trading)\nTrend: {trend}\nCapitale: {round(capitale,2)}€\n\n"
            for t in sorted(risultati, key=lambda x: x["confidence"], reverse=True):
                msg += (
                    f"📌 {t['ticker']} — {t['signal']}\n"
                    f"Entry: {t['entry']}\nStop: {t['stop']}\nTarget: {t['target']}\n"
                    f"Size: {t['size']}\nConfidenza: {t['confidence']}%\nMotivo: {t['reason']}\n\n"
                )
            await bot.send_message(chat_id=CHAT_ID, text=msg)
        else:
            await bot.send_message(chat_id=CHAT_ID,
                                   text=f"📭 Nessun trade valido ora\nTrend: {trend}\nCapitale: {round(capitale,2)}€")

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
