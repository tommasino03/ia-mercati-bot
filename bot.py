import os
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
RISK_REWARD = 2.0

TICKERS = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "TSLA",
    "NVDA", "META", "AMD", "PLTR", "ROKU"
]

# ======================
# UTILS ROBUSTI
# ======================
def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def scalar(x):
    """
    Estrae SEMPRE un float:
    - Series -> ultimo valore
    - DataFrame -> ultima cella
    """
    if x is None:
        return None

    if isinstance(x, pd.DataFrame):
        if x.empty:
            return None
        return float(x.values[-1][0])

    if isinstance(x, pd.Series):
        if x.empty:
            return None
        return float(x.values[-1])

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
# ANALISI TITOLO
# ======================
def analyze(ticker):
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if df.empty or len(df) < 80:
        return None

    df = clean_df(df)

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

    position_size = int((CAPITAL * RISK_PER_TRADE) / last_atr)
    if position_size <= 0:
        return None

    return {
        "ticker": ticker,
        "entry": round(last_close, 2),
        "stop": round(last_close - last_atr, 2),
        "target": round(last_close + last_atr * RISK_REWARD, 2),
        "size": position_size,
        "confidence": round(70 + (45 - last_rsi), 1)
    }

# ======================
# MAIN
# ======================
async def main():
    trades = []

    for t in TICKERS:
        res = analyze(t)
        if res:
            trades.append(res)

    if not trades:
        await bot.send_message(
            chat_id=CHAT_ID,
            text="📭 Nessun trade valido oggi"
        )
        return

    best = sorted(trades, key=lambda x: x["confidence"], reverse=True)[0]

    msg = (
        "🚀 **MIGLIOR TRADE DEL GIORNO**\n\n"
        f"{best['ticker']}\n"
        f"Entry: {best['entry']}\n"
        f"Stop: {best['stop']}\n"
        f"Target: {best['target']}\n"
        f"Size: {best['size']}\n"
        f"Confidenza: {best['confidence']}%\n\n"
        "⚠️ Rispetta SEMPRE lo stop"
    )

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
