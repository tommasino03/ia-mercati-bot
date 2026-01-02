import os
import asyncio
import json
from datetime import datetime

import yfinance as yf
import pandas as pd
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ASSET_FILE = "assets.json"

DEFAULT_ASSETS = ["AAPL", "AMZN", "GOOGL", "META", "NVDA", "SPY", "QQQ"]

# ================= ASSET HANDLING =================
def load_assets():
    if not os.path.exists(ASSET_FILE):
        save_assets(DEFAULT_ASSETS)
        return DEFAULT_ASSETS
    with open(ASSET_FILE, "r") as f:
        return json.load(f)

def save_assets(assets):
    with open(ASSET_FILE, "w") as f:
        json.dump(assets, f)

# ================= DATA =================
def get_data(symbol):
    data = yf.download(symbol, period="6mo", interval="1d", progress=False)
    if data.empty or "Close" not in data:
        return None
    return data["Close"]

# ================= AI SCORE =================
def calculate_score(close: pd.Series):
    if len(close) < 60:
        return 0

    close = close.dropna()
    last = float(close.iloc[-1])

    ema20 = float(close.ewm(span=20).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])

    momentum = (last / float(close.iloc[-20]) - 1) * 100
    volatility = close.pct_change().std() * 100

    score = 0

    if last > ema20 > ema50:
        score += 40
    if momentum > 0:
        score += min(30, momentum)
    if volatility < 2:
        score += 30
    elif volatility < 4:
        score += 15

    return int(min(score, 100))

# ================= OPTIMIZATION =================
def optimize_assets(assets):
    winners = []

    for s in assets:
        close = get_data(s)
        if close is None:
            continue
        score = calculate_score(close)
        if score >= 50:
            winners.append(s)

    return winners if winners else assets

# ================= REPORT =================
def build_alerts(assets):
    text = "🚨 **SEGNALI AI FORTI**\n\n"
    found = False

    for a in assets:
        close = get_data(a)
        if close is None:
            continue

        score = calculate_score(close)
        if score >= 70:
            found = True
            text += f"✅ {a} → SCORE {score}/100\n"

    return text if found else None

# ================= MAIN =================
async def main():
    if not TOKEN or not CHAT_ID:
        raise RuntimeError("Missing secrets")

    bot = Bot(token=TOKEN)
    assets = load_assets()

    # Domenica → ottimizzazione lista
    if datetime.now().weekday() == 6:
        assets = optimize_assets(assets)
        save_assets(assets)
        await bot.send_message(
            chat_id=CHAT_ID,
            text="🧠 Ottimizzazione settimanale completata"
        )

    alerts = build_alerts(assets)
    if alerts:
        await bot.send_message(chat_id=CHAT_ID, text=alerts)

if __name__ == "__main__":
    asyncio.run(main())
