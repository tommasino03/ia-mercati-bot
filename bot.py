import os
import asyncio
from datetime import datetime
from telegram import Bot
import yfinance as yf

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ASSETS_USA = ["AAPL", "AMZN", "GOOGL", "META", "TSLA", "NVDA"]
ETFS = ["SPY", "QQQ"]
EUROPA = ["SAN.MC"]

def analyze(symbol):
    data = yf.download(symbol, period="6mo", interval="1d", progress=False)

    if data.empty or len(data) < 50:
        return f"📌 {symbol}\nDati insufficienti\n\n"

    close = data["Close"].tolist()

    last = close[-1]
    ma20 = sum(close[-20:]) / 20
    ma50 = sum(close[-50:]) / 50

    breve = "✅ COMPRA" if last > ma20 else "⚠️ neutro"
    medio = "✅ COMPRA" if ma20 > ma50 else "⚠️ neutro"
    lungo = "✅ INVESTI" if last > ma50 else "⚠️ neutro"

    return f"""📌 {symbol}
Breve: {breve}
Medio: {medio}
Lungo: {lungo}
"""

def build_report():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI – {now}\n\n"

    report += "--- Azioni USA ---\n"
    for s in ASSETS_USA:
        report += analyze(s)

    report += "\n--- ETF ---\n"
    for s in ETFS:
        report += analyze(s)

    report += "\n--- Azioni Europa ---\n"
    for s in EUROPA:
        report += analyze(s)

    report += """
🧠 SITUAZIONE GENERALE:
Mercato: POSITIVO
Strategia consigliata: COMPRARE SUI RITRACCIAMENTI
Rischio: MEDIO
"""
    return report

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError("BOT_TOKEN o CHAT_ID mancanti")

    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=build_report())

if __name__ == "__main__":
    asyncio.run(main())
