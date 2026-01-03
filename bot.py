import os
import asyncio
import datetime
from telegram import Bot

# PRENDI IL TOKEN E CHAT ID DAI SECRETS
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise RuntimeError("Secrets non trovati. Controlla BOT_TOKEN e CHAT_ID")

# Lista di simboli (puoi personalizzare)
symbols = ["AAPL", "AMZN", "GOOGL", "TSLA", "META"]

def build_report():
    today = datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")
    report = f"📊 REPORT IA MERCATI – {today}\n\n"
    for s in symbols:
        # Analisi semplificata: random consigli per esempio
        breve, medio, lungo = "✅ COMPRA", "✅ COMPRA", "✅ INVESTI"
        report += f"📌 {s}\nBreve: {breve}\nMedio: {medio}\nLungo: {lungo}\nMotivo: trend stabile, volumi regolari\n\n"
    report += "🧠 SITUAZIONE GENERALE:\nMercato: POSITIVO\nStrategia consigliata: COMPRARE SUI RITRACCIAMENTI\nRischio: MEDIO"
    return report

async def main():
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=build_report())

if __name__ == "__main__":
    asyncio.run(main())
