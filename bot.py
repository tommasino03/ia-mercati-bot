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

CAPITAL = 10_000
BASE_RISK_PER_TRADE = 0.01
RISK_REWARD = 2.0
MIN_EDGE = 0.55

TICKERS = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "TSLA",
    "NVDA", "META", "AMD", "PLTR", "ROKU",
    "SOFI", "AFRM", "LCID", "MARA", "RIOT"
]

# ======================
# UTILS
# ======================
def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def scalar(x):
    if isinstance(x, (pd.Series, pd.DataFrame)):
        if len(x) == 0:
            return None
        return float(np.array(x).flatten()[-1])
    return float(x)

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def edge_filter(close, ma20):
    wins = 0
    trades = 0
    for i in range(30, len(close) - 5):
        if close.iloc[i] > ma20.iloc[i]:
            trades += 1
            if close.iloc[i + 5] > close.iloc[i]:
                wins += 1
    return wins / trades if trades > 0 else 0

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
    if scalar(ma50) > scalar(ma200):
        return "UP"
    elif scalar(ma50) < scalar(ma200):
        return "DOWN"
    return "NEUTRAL"

# ======================
# ANALISI TITOLO CON BREAKOUT INTRADAY
# ======================
def analyze(ticker, trend):
    df_daily = yf.download(ticker, period="6mo", interval="1d", progress=False)
    df_hourly = yf.download(ticker, period="30d", interval="60m", progress=False)

    if df_daily.empty or df_hourly.empty or len(df_daily) < 60:
        return None

    df_daily = clean_df(df_daily)
    df_hourly = clean_df(df_hourly)

    close = df_daily["Close"].astype(float)
    high = df_daily["High"].astype(float)
    low = df_daily["Low"].astype(float)
    volume = df_daily["Volume"].astype(float)

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    atr = (high - low).rolling(14).mean()
    rsi_val = scalar(rsi(close))

    # === EDGE FILTER ===
    edge = edge_filter(close, ma20)
    if edge < MIN_EDGE:
        return None

    # === FILTRO RSI DINAMICO ===
    if trend == "UP":
        rsi_threshold = 45
    elif trend == "DOWN":
        rsi_threshold = 55
    else:
        rsi_threshold = 50

    if (trend == "UP" and rsi_val > rsi_threshold) or (trend == "DOWN" and rsi_val < rsi_threshold):
        return None

    last_close = scalar(close)
    last_atr = scalar(atr)

    # === BREAKOUT INTRADAY ===
    intraday_high = df_hourly["High"].max()
    intraday_low = df_hourly["Low"].min()

    breakout = None
    if last_close > intraday_high:
        breakout = "UP"
    elif last_close < intraday_low:
        breakout = "DOWN"

    if not breakout:
        return None

    # === POSIZIONE DINAMICA ===
    risk = BASE_RISK_PER_TRADE * (2 if edge > 0.7 else 1)
    position_size = int((CAPITAL * risk) / last_atr)
    if position_size <= 0:
        return None

    signal = "BUY" if breakout == "UP" else "SELL"

    return {
        "ticker": ticker,
        "signal": signal,
        "entry": round(last_close, 2),
        "stop": round(last_close - last_atr if signal == "BUY" else last_close + last_atr, 2),
        "target": round(last_close + last_atr * RISK_REWARD if signal == "BUY" else last_close - last_atr * RISK_REWARD, 2),
        "size": position_size,
        "edge": round(edge * 100, 1),
        "rsi": round(rsi_val, 1)
    }

# ======================
# MAIN
# ======================
async def main():
    trend = market_trend()
    trades = []

    for t in TICKERS:
        res = analyze(t, trend)
        if res:
            trades.append(res)

    if not trades:
        await bot.send_message(chat_id=CHAT_ID, text=f"📭 Nessuna opportunità oggi\nTrend mercato: {trend}")
        return

    msg = f"🚀 SEGNALI OPERATIVI INTRADAY\nTrend mercato: {trend}\n\n"
    for r in sorted(trades, key=lambda x: x["edge"], reverse=True):
        msg += (
            f"📌 {r['ticker']} — {r['signal']}\n"
            f"Entry: {r['entry']}\n"
            f"Stop: {r['stop']}\n"
            f"Target: {r['target']}\n"
            f"Size: {r['size']}\n"
            f"Edge: {r['edge']}%\n"
            f"RSI: {r['rsi']}\n\n"
        )

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
