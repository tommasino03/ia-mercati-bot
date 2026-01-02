import os
import asyncio
import json
from datetime import datetime

import yfinance as yf
import pandas as pd
from telegram import Bot

# === SECRETS ===
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# === ASSETS ===
ASSETS = {
    "AAPL": "Azioni USA",
    "AMZN": "Azioni USA",
    "GOOGL": "Azioni USA",
    "META": "Azioni USA",
    "NVDA": "Azioni USA",
    "TSLA": "Azioni USA",
    "SPY": "ETF",
    "QQQ": "ETF",
    "BTC-USD": "Crypto",
    "ETH-USD": "Crypto",
}

# === FILE MEMORIA SEGNALI ===
STATE_FILE = "signals_state.json"

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# === CALCOLO TREND E SCORE ===
def calculate_trend(close: pd.Series):
    if close is None or len(close) < 50:
        return "⚠️ neutro", "⚠️ neutro", "⚠️ neutro", 0

    close = close.dropna()
    last = close.iloc[-1].item()
    ema20 = close.ewm(span=20).mean().iloc[-1].item()
    ema50 = close.ewm(span=50).mean().iloc[-1].item()
    ema200 = close.ewm(span=200).mean().iloc[-1].item() if len(close) >= 200 else ema50

    breve = "✅ COMPRA" if last > ema20 else "⚠️ neutro"
    medio = "✅ COMPRA" if last > ema50 else "⚠️ neutro"
    lungo = "✅ INVESTI" if last > ema200 else "⚠️ neutro"

    # Score 0-100 (più segnali positivi → punteggio alto)
    score = sum([breve=="✅ COMPRA", medio=="✅ COMPRA", lungo=="✅ INVESTI"]) * 33
    return breve, medio, lungo, score

# === DECIDE SE INVIARE SEGNALI ===
def should_send_signal(symbol, score, state):
    if score < 60:
        return False  # ignoriamo segnali deboli
    last_score = state.get(symbol, 0)
    if score == last_score:
        return False  # segnale identico già inviato
    state[symbol] = score
    return True

# === ANALISI SINGOLO ASSET ===
def analyze_symbol(symbol, state):
    try:
        data = yf.download(symbol, period="1y", interval="1d", progress=False)
        if data.empty or "Close" not in data:
            return ""

        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        breve, medio, lungo, score = calculate_trend(close)
        if not should_send_signal(symbol, score, state):
            return ""  # niente invio

        return (
            f"\n📌 {symbol}\n"
            f"Breve: {breve}\n"
            f"Medio: {medio}\n"
            f"Lungo: {lungo}\n"
            f"Punteggio: {score}/100\n"
            f"Motivo: trend breve {breve}, trend medio {medio}, trend lungo {lungo}\n"
        )
    except Exception:
        return ""

# === COSTRUISCE IL REPORT COMPLETO ===
def build_report():
    state = load_state()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI – {now}\n"

    categories = {}
    for symbol, category in ASSETS.items():
        categories.setdefault(category, []).append(symbol)

    any_signal = False
    for category, symbols in categories.items():
        category_text = f"\n--- {category} ---\n"
        category_signals = ""
        for s in symbols:
            sig = analyze_symbol(s, state)
            if sig:
                category_signals += sig
        if category_signals:
            any_signal = True
            report += category_text + category_signals

    save_state(state)

    if not any_signal:
        return "🧠 Nessun segnale significativo oggi."

    report += (
        "\n🧠 SITUAZIONE GENERALE:\n"
        "Mercato: POSITIVO\n"
        "Strategia consigliata: COMPRARE SUI RITRACCIAMENTI\n"
        "Rischio: MEDIO"
    )
    return report

# === MAIN ===
async def main():
    if not TOKEN or not CHAT_ID:
        raise RuntimeError("BOT_TOKEN / CHAT_ID mancanti nei Secrets GitHub")

    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=build_report())

if __name__ == "__main__":
    asyncio.run(main())
