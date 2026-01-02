import os
import asyncio
import json
from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ASSETS = ["AAPL", "AMZN", "GOOGL", "META", "NVDA", "SPY", "QQQ"]
STATE_FILE = "signals_state.json"

# ================= UTILS =================
def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ================= STRATEGY =================
def signal_from_price(close: pd.Series):
    ema20 = close.ewm(span=20).mean()
    ema50 = close.ewm(span=50).mean()
    return (ema20 > ema50).astype(int)

def backtest(symbol):
    data = yf.download(symbol, period="6mo", interval="1d", progress=False)
    if data.empty:
        return None

    close = data["Close"]
    signal = signal_from_price(close)

    returns = close.pct_change().fillna(0)
    strat_returns = returns * signal.shift(1).fillna(0)

    cumulative = (1 + strat_returns).prod() - 1
    buy_hold = (1 + returns).prod() - 1
    drawdown = (strat_returns.cumsum() - strat_returns.cumsum().cummax()).min()

    return {
        "symbol": symbol,
        "strategy": round(cumulative * 100, 2),
        "buy_hold": round(buy_hold * 100, 2),
        "drawdown": round(drawdown * 100, 2)
    }

# ================= REPORT =================
def weekly_backtest_report():
    results = []
    for s in ASSETS:
        r = backtest(s)
        if r:
            results.append(r)

    if not results:
        return "📉 BACKTEST\nNessun dato disponibile."

    text = "📈 BACKTEST STRATEGIA (6 MESI)\n"
    for r in results:
        verdict = "✅ BATTE MERCATO" if r["strategy"] > r["buy_hold"] else "❌ SOTTOPERFORMA"
        text += (
            f"\n📌 {r['symbol']}\n"
            f"Strategia: {r['strategy']}%\n"
            f"Buy & Hold: {r['buy_hold']}%\n"
            f"Drawdown: {r['drawdown']}%\n"
            f"Verdetto: {verdict}\n"
        )
    return text

# ================= MAIN =================
async def main():
    if not TOKEN or not CHAT_ID:
        raise RuntimeError("Secrets mancanti")

    bot = Bot(token=TOKEN)

    # Giornaliero
    if datetime.now().weekday() != 6:
        await bot.send_message(
            chat_id=CHAT_ID,
            text="🧠 Bot operativo. Nessuna anomalia rilevata."
        )
        return

    # Domenica → Backtest
    report = weekly_backtest_report()
    await bot.send_message(chat_id=CHAT_ID, text=report)

if __name__ == "__main__":
    asyncio.run(main())
