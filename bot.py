import os
import json
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
RISCHIO_PER_TRADE = 0.02
RISK_REWARD = 2.0
STATO_FILE = "paper_state.json"

TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMD", "META",
    "AMZN", "GOOGL", "TSLA", "PLTR", "ROKU"
]

# ======================
# UTILS SICURI
# ======================
def to_series(x):
    if isinstance(x, pd.DataFrame):
        return x.iloc[:, 0]
    return x

def last_value(x):
    s = to_series(x).dropna()
    if len(s) == 0:
        return None
    return float(s.iloc[-1])

def rsi(series, period=14):
    s = to_series(series)
    delta = s.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def load_state():
    if not os.path.exists(STATO_FILE):
        return {"capitale": CAPITALE_INIZIALE, "trades": []}
    with open(STATO_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATO_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ======================
# TREND MERCATO
# ======================
def market_trend():
    df = yf.download("^GSPC", period="6mo", interval="1d", progress=False)
    if df.empty or len(df) < 200:
        return "NEUTRAL"

    close = to_series(df["Close"])
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()

    if last_value(ma50) > last_value(ma200):
        return "UP"
    elif last_value(ma50) < last_value(ma200):
        return "DOWN"
    return "NEUTRAL"

# ======================
# ANALISI TITOLO
# ======================
def analyze_ticker(ticker, trend, capitale):
    df = yf.download(ticker, period="4mo", interval="1d", progress=False)
    if df.empty or len(df) < 60:
        return None

    close = to_series(df["Close"])
    high = to_series(df["High"])
    low = to_series(df["Low"])

    prezzo = last_value(close)
    if prezzo is None:
        return None

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    rsi_val = last_value(rsi(close))
    atr = last_value((high - low).rolling(14).mean())

    if rsi_val is None or atr is None:
        return None

    motivo = None

    if trend == "UP":
        if prezzo > last_value(ma20) > last_value(ma50) and rsi_val < 50:
            motivo = "Trend rialzista + pullback su forza"

    if not motivo:
        return None

    rischio_euro = capitale * RISCHIO_PER_TRADE
    stop = prezzo - atr
    target = prezzo + atr * RISK_REWARD
    size = int(rischio_euro / (prezzo - stop))

    if size <= 0:
        return None

    return {
        "ticker": ticker,
        "entry": round(prezzo, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "size": size,
        "motivo": motivo,
        "status": "OPEN",
        "open_date": str(datetime.now().date())
    }

# ======================
# GESTIONE TRADE
# ======================
def update_trades(state):
    capitale = state["capitale"]

    for trade in state["trades"]:
        if trade["status"] != "OPEN":
            continue

        df = yf.download(trade["ticker"], period="5d", interval="1d", progress=False)
        if df.empty:
            continue

        close = last_value(df["Close"])
        if close is None:
            continue

        if close <= trade["stop"]:
            capitale += (trade["stop"] - trade["entry"]) * trade["size"]
            trade["status"] = "LOSS"

        elif close >= trade["target"]:
            capitale += (trade["target"] - trade["entry"]) * trade["size"]
            trade["status"] = "WIN"

    state["capitale"] = round(capitale, 2)
    return state

# ======================
# MAIN
# ======================
async def main():
    state = load_state()
    state = update_trades(state)

    trend = market_trend()
    messaggi = []

    for t in TICKERS:
        if any(tr["ticker"] == t and tr["status"] == "OPEN" for tr in state["trades"]):
            continue

        trade = analyze_ticker(t, trend, state["capitale"])
        if trade:
            state["trades"].append(trade)
            messaggi.append(
                f"📈 NUOVO PAPER TRADE\n"
                f"{trade['ticker']}\n"
                f"Entry: {trade['entry']}\n"
                f"Stop: {trade['stop']}\n"
                f"Target: {trade['target']}\n"
                f"Size: {trade['size']}\n"
                f"Motivo: {trade['motivo']}"
            )

    save_state(state)

    if not messaggi:
        messaggi.append(
            f"📭 Nessun trade valido oggi\n"
            f"Trend: {trend}\n"
            f"Capitale: {state['capitale']}€"
        )

    for m in messaggi:
        await bot.send_message(chat_id=CHAT_ID, text=m)

if __name__ == "__main__":
    asyncio.run(main())
