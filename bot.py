import os
import asyncio
import json
from telegram import Bot
import yfinance as yf
import pandas as pd
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")

STATE_FILE = "signals.json"

ASSETS = [
    "AAPL","AMZN","GOOGL","META","TSLA","NVDA",
    "SPY","QQQ","BTC-USD","ETH-USD"
]

# ===== INDICATORI =====
def rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def signal_strength(close: pd.Series):
    close = close.dropna()
    if len(close) < 60:
        return "NEUTRO", 0

    ema20 = close.ewm(span=20).mean()
    ema50 = close.ewm(span=50).mean()
    rsi_val = float(rsi(close).iloc[-1])
    last = float(close.iloc[-1])

    trend_up = last > ema20.iloc[-1] > ema50.iloc[-1]
    trend_down = last < ema20.iloc[-1] < ema50.iloc[-1]

    score = 0
    score += min(abs((last - ema20.iloc[-1]) / ema20.iloc[-1]) * 1000, 30)
    score += min(abs((ema20.iloc[-1] - ema50.iloc[-1]) / ema50.iloc[-1]) * 1000, 30)

    if 40 < rsi_val < 65:
        score += 40
    elif 65 <= rsi_val < 75:
        score += 20

    score = int(min(score, 100))

    if trend_up and score >= 60:
        return "BUY", score
    if trend_down and score >= 60:
        return "SELL", score

    return "NEUTRO", score


# ===== STATO =====
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE) as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ===== ANALISI =====
def analyze():
    previous = load_state()
    current = {}
    alerts = []

    for symbol in ASSETS:
        data = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if data.empty:
            continue

        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        signal, strength = signal_strength(close)
        current[symbol] = signal

        old = previous.get(symbol)
        if signal != "NEUTRO" and old != signal and strength >= 60:
            alerts.append(
                f"📊 {symbol}\n"
                f"Segnale: {signal}\n"
                f"Forza: {strength}/100\n"
            )

    save_state(current)
    return alerts


# ===== MAIN =====
async def main():
    bot = Bot(token=TOKEN)
    alerts = analyze()

    if not alerts:
        return

    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    message = "🔔 ALERT FORTE DI MERCATO\n"
    message += f"🕒 {now}\n\n"
    message += "\n".join(alerts)

    await bot.send_message(chat_id=CHAT_ID, text=message)


if __name__ == "__main__":
    asyncio.run(main())
