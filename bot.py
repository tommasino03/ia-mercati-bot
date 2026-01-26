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

CAPITALE = 1000  # paper trading
RISK_PER_TRADE = 0.02  # 2%
RISK_REWARD = 2.0
MIN_CONFIDENCE = 60

# Universo titoli (liquidi + volatili)
TICKERS = [
    "AAPL","MSFT","NVDA","AMD","META","AMZN","TSLA",
    "PLTR","COIN","RIVN","SOFI","AFRM","SHOP","UBER",
    "SNAP","PYPL","ROKU","MARA","RIOT"
]

# ======================
# UTILS SICURE
# ======================
def last(series):
    s = series.dropna()
    if len(s) == 0:
        return None
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
# TREND MERCATO (S&P500)
# ======================
def market_trend():
    df = yf.download("^GSPC", period="6mo", interval="1d", progress=False)
    if df.empty:
        return "NEUTRAL"

    close = df["Close"]
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()

    if last(ma50) > last(ma200):
        return "UP"
    elif last(ma50) < last(ma200):
        return "DOWN"
    return "NEUTRAL"

# ======================
# ANALISI TITOLI (MOVER LOGICO)
# ======================
def analyze_ticker(ticker, market_trend):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    if df.empty or len(df) < 50:
        return None

    close = df["Close"]
    volume = df["Volume"]

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    rsi_val = last(rsi(close))
    vol_now = last(volume)
    vol_avg = last(volume.rolling(20).mean())

    if None in [rsi_val, vol_now, vol_avg]:
        return None

    price = last(close)

    # ======================
    # FILTRO MOVER
    # ======================
    daily_change = (price - close.iloc[-2]) / close.iloc[-2] * 100

    if daily_change < 4:
        return None

    if vol_now < vol_avg * 1.5:
        return None

    # ======================
    # LOGICA TRADE
    # ======================
    signal = None
    reason = []
    confidence = 50

    if market_trend == "UP" and price > last(ma20) > last(ma50) and rsi_val < 60:
        signal = "BUY"
        confidence += 20
        reason.append("Trend mercato rialzista")
        reason.append("Prezzo sopra MA20 e MA50")
        reason.append("RSI non in ipercomprato")

    if not signal:
        return None

    # ======================
    # RISK MANAGEMENT
    # ======================
    atr = (df["High"] - df["Low"]).rolling(14).mean()
    atr_val = last(atr)
    if atr_val is None:
        return None

    entry = price
    stop = entry - atr_val
    target = entry + atr_val * RISK_REWARD

    risk_amount = CAPITALE * RISK_PER_TRADE
    position_size = risk_amount / (entry - stop)

    return {
        "ticker": ticker,
        "signal": signal,
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "size": int(position_size),
        "confidence": min(confidence, 90),
        "reason": reason
    }

# ======================
# MAIN
# ======================
async def main():
    trend = market_trend()
    trades = []

    for t in TICKERS:
        res = analyze_ticker(t, trend)
        if res and res["confidence"] >= MIN_CONFIDENCE:
            trades.append(res)

    if not trades:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"📭 Nessuna azione oggi\nTrend mercato: {trend}\nCapitale: {CAPITALE}€"
        )
        return

    msg = f"📊 PAPER TRADING — SEGNALI\nTrend mercato: {trend}\nCapitale: {CAPITALE}€\n\n"

    for t in sorted(trades, key=lambda x: x["confidence"], reverse=True)[:3]:
        msg += (
            f"📌 {t['ticker']} — {t['signal']}\n"
            f"Entry: {t['entry']}\n"
            f"Stop: {t['stop']}\n"
            f"Target: {t['target']}\n"
            f"Size: {t['size']} azioni\n"
            f"Confidenza: {t['confidence']}%\n"
            f"Perché:\n"
        )
        for r in t["reason"]:
            msg += f"• {r}\n"
        msg += "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
