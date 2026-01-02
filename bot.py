import os
import asyncio
import json
from telegram import Bot
import yfinance as yf
import pandas as pd
from datetime import datetime

# ====== SECRETS ======
TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")

# ====== FILE STATO ======
STATE_FILE = "signals.json"

# ====== ASSET ======
ASSETS = [
    "AAPL","AMZN","GOOGL","META","TSLA","NVDA",
    "SPY","QQQ","BTC-USD","ETH-USD","SOL-USD"
]

# ====== INDICATORI ======
def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_signal(close: pd.Series):
    close = pd.to_numeric(close, errors="coerce").dropna()
    if len(close) < 50:
        return "NEUTRO"

    ema20 = close.ewm(span=20).mean()
    ema50 = close.ewm(span=50).mean()
    rsi = calculate_rsi(close).iloc[-1]
    last = float(close.iloc[-1])

    if last > ema20.iloc[-1] > ema50.iloc[-1] and rsi < 70:
        return "BUY"
    if last < ema20.iloc[-1] < ema50.iloc[-1]:
        return "SELL"
    return "NEUTRO"


# ====== STATO ======
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ====== ANALISI ======
def analyze():
    previous = load_state()
    current = {}
    alerts = []

    for symbol in ASSETS:
        data = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if data.empty or "Close" not in data:
            continue

        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        signal = calculate_signal(close)
        current[symbol] = signal

        old = previous.get(symbol)
        if old and old != signal:
            alerts.append(f"🚨 {symbol}: {old} ➜ {signal}")

    save_state(current)
    return alerts


# ====== MAIN ======
async def main():
    bot = Bot(token=TOKEN)
    alerts = analyze()

    if not alerts:
        return  # niente spam

    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    message = "🔔 ALERT CAMBIO TREND\n"
    message += f"🕒 {now}\n\n"
    message += "\n".join(alerts)

    await bot.send_message(chat_id=CHAT_ID, text=message)


if __name__ == "__main__":
    asyncio.run(main())
