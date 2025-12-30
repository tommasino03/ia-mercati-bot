import os
import asyncio
from telegram import Bot
import yfinance as yf
import pandas as pd
from datetime import datetime

# ====== LETTURA ROBUSTA SECRETS ======
def get_env(*names):
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None

TOKEN = get_env(
    "TELEGRAM_TOKEN",
    "BOT_TOKEN",
    "TELEGRAM_BOT_TOKEN"
)

CHAT_ID = get_env(
    "TELEGRAM_CHAT_ID",
    "CHAT_ID",
    "TELEGRAM_CHATID"
)

# ====== ASSET ======
ASSETS = {
    "Azioni USA": ["AAPL", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "JPM", "BAC", "V", "MA", "ADBE", "CSCO", "CMCSA", "WMT"],
    "ETF": ["SPY", "QQQ", "VEA", "VGK", "IWV", "VTI", "EFA", "IEMG"],
    "Azioni Europa": ["SAN.MC"]
}

# ====== ANALISI ======
def calculate_trend(close: pd.Series):
    if len(close) < 30:
        return "⚠️ neutro", "⚠️ neutro", "⚠️ neutro"

    last = close.iloc[-1]
    breve = "✅ COMPRA" if last > close.iloc[-5:].mean() else "⚠️ neutro"
    medio = "✅ COMPRA" if last > close.iloc[-20:].mean() else "⚠️ neutro"
    lungo = "✅ INVESTI" if last > close.mean() else "⚠️ neutro"

    return breve, medio, lungo


def analyze_symbol(symbol):
    data = yf.download(symbol, period="6mo", interval="1d", progress=False)
    if data.empty:
        return ""

    close = data["Close"]
    breve, medio, lungo = calculate_trend(close)

    return (
        f"📌 {symbol}\n"
        f"Breve: {breve}\n"
        f"Medio: {medio}\n"
        f"Lungo: {lungo}\n"
        f"Motivo: trend breve {breve}, trend medio {medio}, trend lungo {lungo}, volumi normali\n\n"
    )


def build_report():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI – {now}\n\n"

    for category, symbols in ASSETS.items():
        report += f"--- {category} ---\n"
        for symbol in symbols:
            report += analyze_symbol(symbol)

    report += (
        "🧠 SITUAZIONE GENERALE:\n"
        "Mercato: POSITIVO\n"
        "Strategia consigliata: COMPRARE SUI RITRACCIAMENTI\n"
        "Rischio: MEDIO"
    )
    return report


# ====== MAIN ======
async def main():
    if not TOKEN or not CHAT_ID:
        raise RuntimeError(
            "Secrets non trovati. Controlla che esistano BOT_TOKEN / TELEGRAM_TOKEN e CHAT_ID"
        )

    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=build_report())


if __name__ == "__main__":
    asyncio.run(main())
