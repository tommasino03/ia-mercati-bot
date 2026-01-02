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

# ================= STRATEGY =================
def signal(close: pd.Series):
    ema20 = close.ewm(span=20).mean()
    ema50 = close.ewm(span=50).mean()
    return (ema20 > ema50).astype(int)

def backtest(symbol):
    data = yf.download(symbol, period="6mo", interval="1d", progress=False)
    if data.empty:
        return None

    close = data["Close"]
    sig = signal(close)

    ret = close.pct_change().fillna(0)
    strat = ret * sig.shift(1).fillna(0)

    strat_perf = (1 + strat).prod() - 1
    buy_hold = (1 + ret).prod() - 1

    return strat_perf, buy_hold

# ================= OPTIMIZATION =================
def optimize_assets(assets):
    winners = []

    for s in assets:
        result = backtest(s)
        if not result:
            continue
        strat, hold = result
        if strat > hold:
            winners.append(s)

    return winners if winners else assets

# ================= REPORT =================
def build_report(assets):
    text = "📊 ASSET ATTIVI (AUTO-OTTIMIZZATI)\n"
    for a in assets:
        text += f"• {a}\n"
    return text

# ================= MAIN =================
async def main():
    if not TOKEN or not CHAT_ID:
        raise RuntimeError("Missing secrets")

    bot = Bot(token=TOKEN)
    assets = load_assets()

    # Domenica → ottimizza
    if datetime.now().weekday() == 6:
        assets = optimize_assets(assets)
        save_assets(assets)
        await bot.send_message(
            chat_id=CHAT_ID,
            text="🧠 Ottimizzazione completata"
        )

    await bot.send_message(
        chat_id=CHAT_ID,
        text=build_report(assets)
    )

if __name__ == "__main__":
    asyncio.run(main())
