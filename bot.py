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

CAPITALE = 1000
RISK_PER_TRADE = 0.02
RISK_REWARD = 2.0
MIN_CONFIDENCE = 60

TICKERS = [
    "AAPL","MSFT","NVDA","AMD","META","AMZN","TSLA",
    "PLTR","COIN","RIVN","SOFI","AFRM","SHOP","UBER",
    "SNAP","PYPL","ROKU","MARA","RIOT"
]

# ======================
# UTILS ANTI-CRASH
# ======================
def scalar(x):
    if x is None:
        return None
    if isinstance(x, pd.DataFrame):
        x = x.iloc[:, 0]
    if isinstance(x, pd.Series):
        x = x.dropna()
        if len(x) == 0:
            return None
        return float(x.iloc[-1])
    try:
        return float(x)
    except:
        return None

def rsi(series, period=14):
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
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

    close = df["Close"]
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()

    v50 = scalar(ma50)
    v200 = scalar(ma200)

    if v50 is None or v200 is None:
        return "NEUTRAL"

    if v50 > v200:
        return "UP"
    elif v50 < v200:
        return "DOWN"
    return "NEUTRAL"

# ======================
# ANALISI TITOLO
# ======================
def analyze_ticker(ticker, trend):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    if df.empty or len(df) < 50:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    price = scalar(close)
    prev_price = scalar(close.iloc[:-1])

    if price is None or prev_price is None:
        return None

    daily_change = ((price - prev_price) / prev_price) * 100

    if daily_change < 4:
        return None

    rsi_val = scalar(rsi(close))
    ma20 = scalar(close.rolling(20).mean())
    ma50 = scalar(close.rolling(50).mean())
    vol_now = scalar(volume)
    vol_avg = scalar(volume.rolling(20).mean())

    if None in [rsi_val, ma20, ma50, vol_now, vol_avg]:
        return None

    if vol_now < vol_avg * 1.5:
        return None

    signal = None
    confidence = 50
    reasons = []

    if trend == "UP" and price > ma20 > ma50 and rsi_val < 65:
        signal = "BUY"
        confidence += 30
        reasons = [
            "Trend mercato rialzista",
            "Strong daily mover (>4%)",
            "Prezzo sopra MA20 e MA50",
            "RSI sano (non ipercomprato)",
            "Volume in espansione"
        ]

    if signal is None or confidence < MIN_CONFIDENCE:
        return None

    atr = scalar((high - low).rolling(14).mean())
    if atr is None:
        return None

    entry = price
    stop = entry - atr
    target = entry + atr * RISK_REWARD

    risk_amount = CAPITALE * RISK_PER_TRADE
    size = max(1, int(risk_amount / (entry - stop)))

    return {
        "ticker": ticker,
        "signal": signal,
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "size": size,
        "confidence": min(confidence, 90),
        "reasons": reasons
    }

# ======================
# MAIN
# ======================
async def main():
    trend = market_trend()
    trades = []

    for t in TICKERS:
        res = analyze_ticker(t, trend)
        if res:
            trades.append(res)

    if not trades:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"📭 Nessuna azione oggi\nTrend: {trend}\nCapitale: {CAPITALE}€"
        )
        return

    msg = f"📈 PAPER TRADING\nTrend mercato: {trend}\nCapitale: {CAPITALE}€\n\n"

    for t in sorted(trades, key=lambda x: x["confidence"], reverse=True)[:3]:
        msg += (
            f"📌 {t['ticker']} — {t['signal']}\n"
            f"Entry: {t['entry']}\n"
            f"Stop: {t['stop']}\n"
            f"Target: {t['target']}\n"
            f"Size: {t['size']} azioni\n"
            f"Confidenza: {t['confidence']}%\n"
            f"Motivi:\n"
        )
        for r in t["reasons"]:
            msg += f"• {r}\n"
        msg += "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
