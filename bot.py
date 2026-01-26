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
RISCHIO_PER_TRADE = 0.02  # 2%
RISK_REWARD = 2.0

STATO_FILE = "paper_state.json"

TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMD", "META",
    "AMZN", "GOOGL", "TSLA", "PLTR", "ROKU"
]

# ======================
# UTILS
# ======================
def load_state():
    if not os.path.exists(STATO_FILE):
        return {"capitale": CAPITALE_INIZIALE, "trades": []}
    with open(STATO_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATO_FILE, "w") as f:
        json.dump(state, f, indent=2)

def last(series):
    return float(series.dropna().iloc[-1])

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
    if df.empty or len(df) < 200:
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
# ANALISI TITOLO
# ======================
def analyze_ticker(ticker, trend, capitale):
    df = yf.download(ticker, period="4mo", interval="1d", progress=False)
    if df.empty or len(df) < 60:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    rsi_val = last(rsi(close))
    atr = last((high - low).rolling(14).mean())

    prezzo = last(close)

    motivo = None
    direzione = None

    if trend == "UP":
        if prezzo > last(ma20) > last(ma50) and rsi_val < 50:
            direzione = "BUY"
            motivo = "Trend rialzista + pullback controllato"

    if not direzione:
        return None

    rischio_euro = capitale * RISCHIO_PER_TRADE
    stop = prezzo - atr
    target = prezzo + atr * RISK_REWARD

    size = rischio_euro / (prezzo - stop)

    return {
        "ticker": ticker,
        "direction": direzione,
        "entry": round(prezzo, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "size": int(size),
        "motivo": motivo,
        "open_date": str(datetime.now().date()),
        "status": "OPEN"
    }

# ======================
# GESTIONE TRADE
# ======================
def update_trades(state):
    capitale = state["capitale"]
    nuovi_trades = []

    for trade in state["trades"]:
        if trade["status"] != "OPEN":
            nuovi_trades.append(trade)
            continue

        df = yf.download(trade["ticker"], period="5d", interval="1d", progress=False)
        if df.empty:
            nuovi_trades.append(trade)
            continue

        close = last(df["Close"])

        if close <= trade["stop"]:
            pnl = (trade["stop"] - trade["entry"]) * trade["size"]
            capitale += pnl
            trade["status"] = "LOSS"
            trade["exit_price"] = trade["stop"]

        elif close >= trade["target"]:
            pnl = (trade["target"] - trade["entry"]) * trade["size"]
            capitale += pnl
            trade["status"] = "WIN"
            trade["exit_price"] = trade["target"]

        nuovi_trades.append(trade)

    state["capitale"] = round(capitale, 2)
    state["trades"] = nuovi_trades
    return state

# ======================
# MAIN
# ======================
async def main():
    state = load_state()
    state = update_trades(state)

    trend = market_trend()
    aperti = [t for t in state["trades"] if t["status"] == "OPEN"]

    messaggi = []

    for t in TICKERS:
        if any(tr["ticker"] == t and tr["status"] == "OPEN" for tr in aperti):
            continue

        trade = analyze_ticker(t, trend, state["capitale"])
        if trade:
            state["trades"].append(trade)
            messaggi.append(
                f"📈 NUOVO TRADE PAPER\n"
                f"{trade['ticker']} — {trade['direction']}\n"
                f"Entry: {trade['entry']}\n"
                f"Stop: {trade['stop']}\n"
                f"Target: {trade['target']}\n"
                f"Size: {trade['size']}\n"
                f"Motivo: {trade['motivo']}"
            )

    save_state(state)

    if not messaggi:
        messaggi.append(
            f"📭 Nessuna azione oggi\n"
            f"Trend: {trend}\n"
            f"Capitale: {state['capitale']}€"
        )

    for msg in messaggi:
        await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
