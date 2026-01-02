import os
import asyncio
import json
from datetime import datetime

import yfinance as yf
import pandas as pd
from telegram import Bot

# ================= SECRETS =================
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ASSET_FILE = "assets.json"
DEFAULT_ASSETS = ["AAPL", "AMZN", "GOOGL", "META", "NVDA", "SPY", "QQQ"]

# ================= ASSETS =================
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
def get_close(symbol):
    df = yf.download(symbol, period="6mo", interval="1d", progress=False)
    if df.empty or "Close" not in df:
        return None
    return df["Close"].dropna()

# ================= AI SCORE =================
def calculate_score(close: pd.Series) -> int:
    if len(close) < 60:
        return 0

    last = close.iloc[-1]

    ema20 = close.ewm(span=20).mean().iloc[-1]
    ema50 = close.ewm(span=50).mean().iloc[-1]

    momentum = (last / close.iloc[-20] - 1) * 100
    volatility = close.pct_change().std()

    score = 0

    if last > ema20 and ema20 > ema50:
        score += 40

    if momentum > 0:
        score += min(30, int(momentum))

    if volatility < 0.02:
        score += 30
    elif volatility < 0.04:
        score += 15

    return min(score, 100)

# ================= OPTIMIZATION =================
def optimize_assets(assets):
    selected = []

    for s in assets:
        close = get_close(s)
        if close is None:
            continue
        if calculate_score(close) >= 50:
            selected.append(s)

    return selected if selected else assets

# ================= ALERTS =================
def build_alerts(assets):
    lines = []

    for s in assets:
        close = get_close(s)
        if close is None:
            continue

        score = calculate_score(close)
        if score >= 70:
            lines.append(f"✅ {s} → SCORE {score}/100")

    if not lines:
        return None

    return "🚨 SEGNALI AI FORTI\n\n" + "\n".join(lines)

# ================= MAIN =================
async def main():
    if not TOKEN or not CHAT_ID:
        raise RuntimeError("Secrets mancanti")

    bot = Bot(token=TOKEN)
    assets = load_assets()

    # Domenica: ottimizzazione
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
