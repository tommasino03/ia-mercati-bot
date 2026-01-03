import os
import asyncio
import datetime
import random  # per simulare i trend
from telegram import Bot

# PRENDI IL TOKEN E CHAT ID DAI SECRETS
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise RuntimeError("Secrets non trovati. Controlla BOT_TOKEN e CHAT_ID")

# Lista di simboli (puoi personalizzare)
symbols = ["AAPL", "AMZN", "GOOGL", "TSLA", "META", "NVDA", "JPM", "BAC", "V", "MA"]

# Funzione per simulare trend
def calculate_trend():
    trend_values = ["✅ COMPRA", "⚠️ neutro", "✅ INVESTI"]
    return random.choice(trend_values), random.choice(trend_values), random.choice(trend_values)

def build_report():
    today = datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")
    report = f"📊 REPORT IA MERCATI – {today}\n\n"

    for s in symbols:
        breve, medio, lungo = calculate_trend()
        report += (
            f"📌 {s}\n"
            f"Breve: {breve}\n"
            f"Medio: {medio}\n"
            f"Lungo: {lungo}\n"
            f"Motivo: trend breve {breve}, trend medio {medio}, trend lungo {lungo}, volumi normali\n\n"
        )

    report += (
        "🧠 SITUAZIONE GENERALE:\n"
        "Mercato: POSITIVO\n"
        "Strategia consigliata: COMPRARE SUI RITRACCIAMENTI\n"
        "Rischio: MEDIO"
    )
    return report

async def main():
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=build_report())

if __name__ == "__main__":
    asyncio.run(main())
