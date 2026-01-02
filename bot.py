import os
import json
import asyncio
from datetime import datetime

import yfinance as yf
import pandas as pd
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
STATE_FILE = "state.json"

ASSETS = {
    "Azioni USA": [
        "AAPL", "AMZN", "GOOGL", "META", "TSLA", "NVDA",
        "JPM", "BAC", "V", "MA", "ADBE", "CSCO", "CMCSA", "WMT"
    ],
    "ETF": [
        "SPY", "QQQ", "VEA", "VGK", "IWV", "VTI", "EFA", "IEMG"
    ],
    "Azioni Europa": [
        "SAN.MC"
    ]
}


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def calculate_trend(close: pd.Series):
    close = close.dropna()

    if len(close) < 60:
        return "⚠️ neutro", "⚠️ neutro", "⚠️ neutro"

    last = float(close.iloc[-1])
    ema20 = float(close.ewm(span=20).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])
    ema200 = float(close.ewm(span=200).mean().iloc[-1])

    breve = "✅ COMPRA" if last > ema20 else "⚠️ neutro"
    medio = "✅ COMPRA" if ema20 > ema50 else "⚠️ neutro"
    lungo = "✅ INVESTI" if ema50 > ema200 else "⚠️ neutro"

    return breve, medio, lungo


def calculate_score(trend_tuple):
    score = 0
    breve, medio, lungo = trend_tuple
    score += 1 if breve == "✅ COMPRA" else 0
    score += 1 if medio == "✅ COMPRA" else 0
    score += 1 if lungo == "✅ INVESTI" else 0
    return score


def analyze_symbol(symbol: str, prev_state: dict):
    data = yf.download(symbol, period="1y", interval="1d", progress=False)

    if data.empty or "Close" not in data:
        return None, None, None

    trend = calculate_trend(data["Close"])
    score = calculate_score(trend)
    current_state = {"breve": trend[0], "medio": trend[1], "lungo": trend[2], "score": score}

    if prev_state.get(symbol) == current_state:
        return None, None, None

    message = (
        f"📌 {symbol}\n"
        f"Breve: {trend[0]}\n"
        f"Medio: {trend[1]}\n"
        f"Lungo: {trend[2]}\n"
        f"Score: {score}/3\n\n"
    )

    return symbol, current_state, message


async def main():
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError("BOT_TOKEN o CHAT_ID mancanti")

    bot = Bot(token=BOT_TOKEN)
    state = load_state()
    new_state = state.copy()

    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 ALERT IA MERCATI – {now}\n\n"
    changed = False
    ranking = []

    for section, symbols in ASSETS.items():
        section_text = ""
        for s in symbols:
            result = analyze_symbol(s, state)
            if result and result[0]:
                symbol, current, msg = result
                new_state[symbol] = current
                section_text += msg
                changed = True
                ranking.append((symbol, current["score"]))

        if section_text:
            report += f"--- {section} ---\n{section_text}"

    # TOP 5 ASSETS
    if ranking:
        ranking_sorted = sorted(ranking, key=lambda x: x[1], reverse=True)[:5]
        report += "--- TOP 5 ASSETS DEL GIORNO ---\n"
        for sym, score in ranking_sorted:
            report += f"📌 {sym} → Score: {score}/3\n"

    if changed:
        report += (
            "\n🧠 STRATEGIA:\n"
            "Segnali aggiornati → valuta ingresso sui ritracciamenti\n"
            "Rischio: MEDIO\n"
        )
        await bot.send_message(chat_id=CHAT_ID, text=report)
        save_state(new_state)


if __name__ == "__main__":
    asyncio.run(main())
