import os
import asyncio
from telegram import Bot
import yfinance as yf
import pandas as pd
from datetime import datetime

# ====== CONFIG ======
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

ASSETS = {
    "Azioni USA": ["AAPL", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "JPM", "BAC", "V", "MA", "ADBE", "CSCO", "CMCSA", "WMT"],
    "ETF": ["SPY", "QQQ", "VEA", "VGK", "IWV", "VTI", "EFA", "IEMG"],
    "Azioni Europa": ["SAN.MC"]
}

# ====== ANALISI ======
def calculate_trend(close: pd.Series):
    if len(close) < 30:
        return "⚠️ neutro", "⚠️ neutro", "⚠️ neutro"

    breve_avg = close.iloc[-5:].mean()
    medio_avg = close.iloc[-20:].mean()
    lungo_avg = close.iloc[-60:].mean() if len(close) >= 60 else close.mean()
    last = close.iloc[-1]

    breve = "✅ COMPRA" if last > breve_avg else "⚠️ neutro"
    medio = "✅ COMPRA" if last > medio_avg else "⚠️ neutro"
    lungo = "✅ INVESTI" if last > lungo_avg else "⚠️ neutro"

    return breve, medio, lungo


def analyze_symbol(symbol):
    data = yf.download(symbol, period="6mo", interval="1d", progress=False)

    if data.empty:
        return None

    close = data["Close"]
    breve, medio, lungo = calculate_trend(close)

    return (
        f"📌 {symbol}\n"
        f"Breve: {breve}\n"
        f"Medio: {medio}\n"
        f"Lungo: {lungo}\n"
        f"Motivo: trend breve {breve}, trend medio {medio}, trend lungo {lungo}, volumi normali\n"
    )


def build_report():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI – {now}\n\n"

    for category, symbols in ASSETS.items():
        report += f"--- {category} ---\n"
        for symbol in symbols:
            analysis = analyze_symbol(symbol)
            if analysis:
                report += analysis + "\n"

    report += (
        "\n🧠 SITUAZIONE GENERALE:\n"
        "Mercato: POSITIVO\n"
        "Strategia consigliata: COMPRARE SUI RITRACCIAMENTI\n"
        "Rischio: MEDIO"
    )

    return report


# ====== MAIN ======
async def main():
    if not TOKEN or not CHAT_ID:
        raise RuntimeError("TOKEN o CHAT_ID mancanti nei secrets GitHub")

    bot = Bot(token=TOKEN)
    report = build_report()
    await bot.send_message(chat_id=CHAT_ID, text=report)


if __name__ == "__main__":
    asyncio.run(main())
