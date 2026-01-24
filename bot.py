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
MIN_CONFIDENCE = 65  # %
CAPITALE = 1000  # capitale iniziale per paper trading

# ======================
# UTILS
# ======================
def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def last(x):
    arr = np.array(x)
    if len(arr.shape) > 1:  # se è DataFrame
        return float(arr[-1, 0])
    return float(arr[-1])

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
# ANALISI TITOLO + MOVERS + PAPER TRADING
# ======================
def analyze(ticker, trend, capitale):
    df = yf.download(ticker, period="4mo", interval="1d", progress=False)
    if df.empty or len(df) < 60:
        return None, capitale

    df = clean_df(df)
    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    volume = df["Volume"].astype(float)
    open_price = df["Open"].astype(float)

    rsi_val = last(rsi(close))
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    atr_val = last((high - low).rolling(14).mean())

    # ======================
    # MOVERS GIORNALIERI
    # ======================
    daily_change_pct = (last(close) - last(open_price)) / last(open_price) * 100
    is_mover = abs(daily_change_pct) >= 3  # soglia %

    signal = None
    confidence = 0

    # ======================
    # LOGICA TRADE
    # ======================
    if trend == "UP":
        if last(close) > last(ma20) > last(ma50) and rsi_val < 45:
            signal = "BUY"
            confidence = 70 + (45 - rsi_val)
    elif trend == "DOWN":
        if last(close) < last(ma20) < last(ma50) and rsi_val > 55:
            signal = "SELL"
            confidence = 70 + (rsi_val - 55)

    # Se non ci sono segnali classici ma il titolo è mover
    if not signal and is_mover:
        signal = "BUY" if daily_change_pct > 0 else "SELL"
        confidence = min(85, 50 + abs(daily_change_pct) * 5)

    if not signal or confidence < MIN_CONFIDENCE:
        return None, capitale

    entry = last(close)
    if signal == "BUY":
        stop = entry - atr_val
        target = entry + atr_val * RISK_REWARD
    else:
        stop = entry + atr_val
        target = entry - atr_val * RISK_REWARD

    # ======================
    # PAPER TRADING
    # ======================
    # calcolo numero azioni da comprare in base al capitale disponibile
    qty = max(1, int(capitale / entry))
    # aggiorno capitale ipotetico
    capitale -= qty * entry

    trade_info = {
        "ticker": ticker,
        "signal": signal,
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "confidence": round(min(confidence, 95), 1),
        "qty": qty,
        "mover": is_mover
    }

    return trade_info, capitale

# ======================
# MAIN
# ======================
async def main():
    trend = market_trend()
    capitale = CAPITALE
    results = []

    for t in TICKERS:
        r, capitale = analyze(t, trend, capitale)
        if r:
            results.append(r)

    if not results:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"📭 Nessun trade valido oggi\nTrend mercato: {trend}\nCapitale residuo: {capitale:.2f}$"
        )
        return

    msg = f"🚀 SEGNALI OPERATIVI (Paper trading)\nTrend mercato: {trend}\nCapitale iniziale: {CAPITALE}$\nCapitale residuo: {capitale:.2f}$\n\n"

    for r in sorted(results, key=lambda x: x["confidence"], reverse=True):
        msg += (
            f"📌 {r['ticker']} — {r['signal']}\n"
            f"Entry: {r['entry']}$\n"
            f"Stop: {r['stop']}$\n"
            f"Target: {r['target']}$\n"
            f"Quantità: {r['qty']}\n"
            f"Confidenza: {r['confidence']}%\n"
            f"Mover: {'✅' if r['mover'] else '❌'}\n\n"
        )

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
