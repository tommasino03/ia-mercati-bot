import os
import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import Bot
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

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

CONFIDENCE_THRESHOLD = 0.65
RISK_REWARD = 2.0

# ======================
# UTILS
# ======================
def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def last(x):
    return float(np.asarray(x)[-1])

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ======================
# FEATURE ENGINEERING
# ======================
def build_features(df):
    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    volume = df["Volume"].astype(float)

    df_feat = pd.DataFrame()
    df_feat["rsi"] = rsi(close)
    df_feat["ma20"] = close.rolling(20).mean()
    df_feat["ma50"] = close.rolling(50).mean()
    df_feat["price_ma20"] = close / df_feat["ma20"]
    df_feat["price_ma50"] = close / df_feat["ma50"]
    df_feat["vol_ratio"] = volume / volume.rolling(20).mean()
    df_feat["atr"] = (high - low).rolling(14).mean()

    df_feat["future_return"] = close.shift(-5) / close - 1
    df_feat["target"] = (df_feat["future_return"] > 0).astype(int)

    return df_feat.dropna()

# ======================
# TRAIN ML MODEL
# ======================
def train_model(ticker):
    df = yf.download(ticker, period="2y", interval="1d", progress=False)
    if df.empty or len(df) < 200:
        return None, None

    df = clean_df(df)
    data = build_features(df)

    X = data.drop(columns=["future_return", "target"])
    y = data["target"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(max_iter=500)
    model.fit(X_scaled, y)

    return model, scaler

# ======================
# ANALISI LIVE
# ======================
def analyze_ticker(ticker):
    model, scaler = train_model(ticker)
    if not model:
        return None

    df = yf.download(ticker, period="4mo", interval="1d", progress=False)
    df = clean_df(df)

    feat = build_features(df)
    latest = feat.iloc[-1:].drop(columns=["future_return", "target"])

    X_live = scaler.transform(latest)
    prob_up = model.predict_proba(X_live)[0][1]

    close = df["Close"].astype(float)
    atr = (df["High"] - df["Low"]).rolling(14).mean()

    entry = last(close)
    atr_val = last(atr)

    if prob_up >= CONFIDENCE_THRESHOLD:
        signal = "BUY"
        stop = entry - atr_val
        target = entry + atr_val * RISK_REWARD
    elif prob_up <= 1 - CONFIDENCE_THRESHOLD:
        signal = "SELL"
        stop = entry + atr_val
        target = entry - atr_val * RISK_REWARD
    else:
        return None

    return {
        "ticker": ticker,
        "signal": signal,
        "confidence": round(prob_up * 100, 1),
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "target": round(target, 2)
    }

# ======================
# MAIN
# ======================
async def main():
    results = []

    for t in TICKERS:
        res = analyze_ticker(t)
        if res:
            results.append(res)

    if not results:
        await bot.send_message(
            chat_id=CHAT_ID,
            text="📭 Nessun segnale ML valido oggi"
        )
        return

    msg = "🤖 SEGNALI ML (Adaptive)\n\n"

    for r in sorted(results, key=lambda x: x["confidence"], reverse=True):
        msg += (
            f"📌 {r['ticker']} — {r['signal']}\n"
            f"Entry: {r['entry']}\n"
            f"Stop: {r['stop']}\n"
            f"Target: {r['target']}\n"
            f"Probabilità: {r['confidence']}%\n\n"
        )

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
