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
    raise ValueError("❌ Token Telegram mancanti")

bot = Bot(token=TOKEN)

STATE_FILE = "paper_state.csv"

CAPITALE_INIZIALE = 10000
RISK_PER_TRADE = 0.02
RISK_REWARD = 2.0
MIN_CONFIDENCE = 70

TICKERS = [
    "AAPL", "MSFT", "NVDA", "TSLA",
    "AMD", "META", "AMZN", "PLTR", "SOFI"
]

# ======================
# UTILS SICURI
# ======================
def last(series):
    return float(series.iloc[-1])

def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ======================
# STATO PAPER TRADING
# ======================
def load_state():
    if not os.path.exists(STATE_FILE):
        return {
            "capital": CAPITALE_INIZIALE,
            "positions": []
        }
    df = pd.read_csv(STATE_FILE)
    positions = df.to_dict("records")
    capital = positions[0]["capital"]
    return {"capital": capital, "positions": positions}

def save_state(state):
    if not state["positions"]:
        df = pd.DataFrame([{
            "capital": state["capital"],
            "ticker": "",
            "side": "",
            "entry": 0,
            "stop": 0,
            "target": 0,
            "qty": 0,
            "open_date": ""
        }])
    else:
        df = pd.DataFrame(state["positions"])
    df.to_csv(STATE_FILE, index=False)

# ======================
# TREND MERCATO
# ======================
def market_trend():
    df = yf.download("^GSPC", period="6mo", interval="1d", progress=False)
    if df.empty:
        return "NEUTRAL"
    df = clean_df(df)
    close = df["Close"]
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()
    return "UP" if last(ma50) > last(ma200) else "DOWN"

# ======================
# ANALISI TRADE
# ======================
def analyze(ticker, trend):
    df = yf.download(ticker, period="4mo", interval="1d", progress=False)
    if df.empty or len(df) < 60:
        return None

    df = clean_df(df)
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    rsi_val = last(rsi(close))
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    atr = (high - low).rolling(14).mean()

    signal = None
    confidence = 0

    if trend == "UP" and last(close) > last(ma20) > last(ma50) and rsi_val < 50:
        signal = "BUY"
        confidence = 75 + (50 - rsi_val)

    if not signal or confidence < MIN_CONFIDENCE:
        return None

    entry = last(close)
    stop = entry - last(atr)
    target = entry + last(atr) * RISK_REWARD

    return {
        "ticker": ticker,
        "side": signal,
        "entry": entry,
        "stop": stop,
        "target": target,
        "confidence": round(confidence, 1)
    }

# ======================
# PAPER TRADING ENGINE
# ======================
def position_size(capital, entry, stop):
    risk = abs(entry - stop)
    if risk == 0:
        return 0
    return int((capital * RISK_PER_TRADE) / risk)

# ======================
# MAIN
# ======================
async def main():
    state = load_state()
    capital = state["capital"]
    positions = state["positions"]
    messages = []

    # 🔴 CONTROLLO POSIZIONI APERTE
    new_positions = []
    for p in positions:
        if not p["ticker"]:
            continue

        df = yf.download(p["ticker"], period="5d", interval="1d", progress=False)
        if df.empty:
            new_positions.append(p)
            continue

        price = last(df["Close"])
        pnl = 0

        if price <= p["stop"]:
            pnl = (p["stop"] - p["entry"]) * p["qty"]
            capital += pnl
            messages.append(
                f"🔴 CHIUSA {p['ticker']} STOP\nRisultato: {round(pnl,2)} €\nCapitale: {round(capital,2)} €"
            )
        elif price >= p["target"]:
            pnl = (p["target"] - p["entry"]) * p["qty"]
            capital += pnl
            messages.append(
                f"🟢 CHIUSA {p['ticker']} TARGET\nRisultato: {round(pnl,2)} €\nCapitale: {round(capital,2)} €"
            )
        else:
            new_positions.append(p)

    positions = new_positions

    # 🟢 NUOVE APERTURE
    trend = market_trend()
    for t in TICKERS:
        if any(p["ticker"] == t for p in positions):
            continue

        trade = analyze(t, trend)
        if trade:
            qty = position_size(capital, trade["entry"], trade["stop"])
            if qty <= 0:
                continue

            positions.append({
                "capital": capital,
                "ticker": trade["ticker"],
                "side": trade["side"],
                "entry": trade["entry"],
                "stop": trade["stop"],
                "target": trade["target"],
                "qty": qty,
                "open_date": datetime.now().strftime("%Y-%m-%d")
            })

            messages.append(
                f"🟢 APERTA {trade['ticker']} BUY\n"
                f"Entry: {round(trade['entry'],2)}\n"
                f"Stop: {round(trade['stop'],2)}\n"
                f"Target: {round(trade['target'],2)}\n"
                f"Qty: {qty}\n"
                f"Capitale: {round(capital,2)} €"
            )

    state["capital"] = capital
    state["positions"] = positions
    save_state(state)

    if messages:
        await bot.send_message(chat_id=CHAT_ID, text="\n\n".join(messages))
    else:
        await bot.send_message(chat_id=CHAT_ID, text=f"📭 Nessuna azione oggi\nCapitale: {round(capital,2)} €")

if __name__ == "__main__":
    asyncio.run(main())
