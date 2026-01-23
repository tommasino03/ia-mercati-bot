import os
import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import Bot
from datetime import datetime, timedelta

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
MIN_CONFIDENCE = 65
LOOKAHEAD_DAYS = 5
TRADES_FILE = "trades.csv"
EXCLUDED_FILE = "excluded.csv"

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

def atr(high, low, period=14):
    return (high - low).rolling(period).mean()

# ======================
# MARKET TREND
# ======================
def market_trend():
    df = yf.download("^GSPC", period="6mo", interval="1d", progress=False)
    if df.empty:
        return "NEUTRAL"

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
# SIGNAL GENERATION MULTI-TIMEFRAME
# ======================
def analyze(ticker, trend, excluded):
    if ticker in excluded:
        return None

    # timeframe daily
    df_daily = yf.download(ticker, period="4mo", interval="1d", progress=False)
    # timeframe weekly
    df_weekly = yf.download(ticker, period="12mo", interval="1wk", progress=False)

    if df_daily.empty or len(df_daily) < 60 or df_weekly.empty:
        return None

    df_daily = clean_df(df_daily)
    df_weekly = clean_df(df_weekly)

    close = df_daily["Close"]
    high = df_daily["High"]
    low = df_daily["Low"]

    # Daily indicators
    rsi_val = last(rsi(close))
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    atr_val = last(atr(high, low))

    # Weekly trend confirmation
    weekly_close = df_weekly["Close"]
    weekly_ma20 = weekly_close.rolling(20).mean()
    weekly_ma50 = weekly_close.rolling(50).mean()

    weekly_trend_ok = (last(weekly_ma20) > last(weekly_ma50) and trend=="UP") or \
                      (last(weekly_ma20) < last(weekly_ma50) and trend=="DOWN")

    if not weekly_trend_ok:
        return None

    signal = None
    confidence = 0

    # LOGICA TRADE
    if trend == "UP" and last(close) > last(ma20) > last(ma50) and rsi_val < 45:
        signal = "BUY"
        confidence = 70 + (45 - rsi_val)
    elif trend == "DOWN" and last(close) < last(ma20) < last(ma50) and rsi_val > 55:
        signal = "SELL"
        confidence = 70 + (rsi_val - 55)

    if not signal or confidence < MIN_CONFIDENCE:
        return None

    # Score combinato con ATR (volatilità)
    score = confidence * (1 - min(atr_val/last(close),0.2))  # penalizza titoli troppo volatili

    entry = last(close)
    if signal == "BUY":
        stop = entry - atr_val
        target = entry + atr_val * RISK_REWARD
    else:
        stop = entry + atr_val
        target = entry - atr_val * RISK_REWARD

    return {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "ticker": ticker,
        "signal": signal,
        "entry": round(entry,2),
        "stop": round(stop,2),
        "target": round(target,2),
        "confidence": round(confidence,1),
        "score": round(score,1),
        "status": "OPEN"
    }

# ======================
# TRADE TRACKING
# ======================
def update_trades():
    excluded = []
    if os.path.exists(EXCLUDED_FILE):
        excluded = pd.read_csv(EXCLUDED_FILE)["ticker"].tolist()

    if not os.path.exists(TRADES_FILE):
        return excluded, pd.DataFrame()

    trades = pd.read_csv(TRADES_FILE)
    updated = False

    for i, t in trades.iterrows():
        if t["status"] != "OPEN":
            continue

        df = yf.download(
            t["ticker"],
            start=t["date"],
            end=(datetime.strptime(t["date"], "%Y-%m-%d") + timedelta(days=LOOKAHEAD_DAYS)).strftime("%Y-%m-%d"),
            interval="1d",
            progress=False
        )
        if df.empty:
            continue

        df = clean_df(df)
        high = df["High"].max()
        low = df["Low"].min()

        if t["signal"] == "BUY":
            if high >= t["target"]:
                trades.at[i, "status"] = "WIN"
                updated = True
            elif low <= t["stop"]:
                trades.at[i, "status"] = "LOSS"
                updated = True
                excluded.append(t["ticker"])
        else:
            if low <= t["target"]:
                trades.at[i, "status"] = "WIN"
                updated = True
            elif high >= t["stop"]:
                trades.at[i, "status"] = "LOSS"
                updated = True
                excluded.append(t["ticker"])

    if updated:
        trades.to_csv(TRADES_FILE, index=False)
        if excluded:
            pd.DataFrame({"ticker": list(set(excluded))}).to_csv(EXCLUDED_FILE, index=False)

    return excluded, trades

# ======================
# MAIN
# ======================
async def main():
    trend = market_trend()
    excluded, trades = update_trades()
    new_trades = []

    for t in TICKERS:
        res = analyze(t, trend, excluded)
        if res:
            new_trades.append(res)

    if new_trades:
        df_new = pd.DataFrame(new_trades)
        if os.path.exists(TRADES_FILE):
            df_old = pd.read_csv(TRADES_FILE)
            df_all = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_all = df_new
        df_all.to_csv(TRADES_FILE, index=False)

    closed = trades[trades["status"].isin(["WIN","LOSS"])] if not trades.empty else pd.DataFrame()
    win_rate = round(len(closed[closed["status"]=="WIN"])/len(closed)*100,1) if not closed.empty else 0

    msg = f"📊 REPORT PERFORMANCE\nTrend mercato: {trend}\n\n"
    msg += f"Trade chiusi: {len(closed)}\nWin rate: {win_rate}%\n"
    msg += f"Tickers esclusi (LOSS): {', '.join(excluded) if excluded else 'nessuno'}\n\n"
    msg += "🚀 Segnali attivi:\n"
    if new_trades:
        for r in sorted(new_trades, key=lambda x: x["score"], reverse=True):
            msg += (f"📌 {r['ticker']} — {r['signal']} | Conf: {r['confidence']} | Score: {r['score']}\n"
                    f"Entry: {r['entry']} | Stop: {r['stop']} | Target: {r['target']}\n\n")
    else:
        msg += "Nessun segnale valido oggi"

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
