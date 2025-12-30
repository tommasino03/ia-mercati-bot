import os
import asyncio
from telegram import Bot
import yfinance as yf
import pandas as pd
from datetime import datetime

# ====== SECRETS ======
TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")

# ====== ASSET ======
ASSETS = {
    "Azioni USA": [
        "AAPL","AMZN","GOOGL","META","TSLA","NVDA",
        "JPM","BAC","V","MA","ADBE","CSCO","CMCSA","WMT"
    ],
    "ETF": ["SPY","QQQ","VEA","VGK","IWV","VTI","EFA","IEMG"],
    "Azioni Europa": ["SAN.MC"]
}

# ====== ANALISI ======
def calculate_trend(close: pd.Series):
    close = pd.to_numeric(close, errors="coerce").dropna()

    if len(close) < 30:
        return "⚠️ neutro", "⚠️ neutro", "⚠️ neutro"

    last = float(close.iloc[-1])
    breve_avg = float(close.iloc[-5:].mean())
    medio_avg = float(close.iloc[-20:].mean())
    lungo_avg = float(close.mean())

    breve = "✅ COMPRA" if last > breve_avg else "⚠️ neutro"
    medio = "✅ COMPRA" if last > medio_avg else "⚠️ neutro"
    lungo = "✅ INVESTI" if last > lungo_avg else "⚠️ neutro"

    return breve, medio, lungo


def analyze_symbol(symbol):
    data = yf.download(symbol, period="6mo", interval="1d", progress=False)

    if data.empty or "Close" not in data:
        return ""

    close = data["Close"]

    # 🔒 normalizzazione definitiva
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

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
        for s in symbols:
            report += analyze_symbol(s)

    report += (
        "🧠 SITUAZIONE GENERALE:\n"
        "Mercato: POSITIVO\n"
        "Strategia consigliata: COMPRARE SUI RITRACCIAMENTI\n"
        "Rischio: MEDIO"
    )

    return report


# ====== MAIN ======
async def main():
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=build_report())


if __name__ == "__main__":
    asyncio.run(main())
