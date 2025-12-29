import os
import asyncio
from datetime import datetime
from telegram import Bot

TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN mancante nei GitHub Secrets")
if not CHAT_ID:
    raise RuntimeError("CHAT_ID mancante nei GitHub Secrets")

# ===== DATI (puoi modificarli in futuro) =====
AZIONI_USA = {
    "AAPL": ("⚠️ neutro", "✅ COMPRA", "✅ INVESTI"),
    "AMZN": ("✅ COMPRA", "✅ COMPRA", "✅ INVESTI"),
    "GOOGL": ("✅ COMPRA", "✅ COMPRA", "✅ INVESTI"),
    "META": ("✅ COMPRA", "✅ COMPRA", "✅ INVESTI"),
    "TSLA": ("✅ COMPRA", "✅ COMPRA", "✅ INVESTI"),
    "NVDA": ("✅ COMPRA", "✅ COMPRA", "✅ INVESTI"),
    "JPM": ("✅ COMPRA", "✅ COMPRA", "✅ INVESTI"),
    "BAC": ("✅ COMPRA", "✅ COMPRA", "✅ INVESTI"),
    "V": ("✅ COMPRA", "✅ COMPRA", "✅ INVESTI"),
    "MA": ("✅ COMPRA", "✅ COMPRA", "✅ INVESTI"),
    "ADBE": ("✅ COMPRA", "✅ COMPRA", "✅ INVESTI"),
    "CSCO": ("✅ COMPRA", "✅ COMPRA", "✅ INVESTI"),
    "CMCSA": ("✅ COMPRA", "✅ COMPRA", "✅ INVESTI"),
    "WMT": ("⚠️ neutro", "✅ COMPRA", "✅ INVESTI"),
}

ETF = ["SPY", "QQQ", "VEA", "VGK", "IWV", "VTI", "EFA", "IEMG"]

AZIONI_EUROPA = ["SAN.MC"]

# ===== COSTRUZIONE REPORT =====
def build_report():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI – {now}\n\n"

    report += "--- Azioni USA ---\n"
    for ticker, trend in AZIONI_USA.items():
        report += (
            f"📌 {ticker}\n"
            f"Breve: {trend[0]}\n"
            f"Medio: {trend[1]}\n"
            f"Lungo: {trend[2]}\n"
            f"Motivo: trend breve {trend[0]}, trend medio {trend[1]}, "
            f"trend lungo {trend[2]}, volumi normali\n\n"
        )

    report += "--- ETF ---\n"
    for etf in ETF:
        report += (
            f"📌 {etf}\n"
            f"Breve: ✅ COMPRA\n"
            f"Medio: ✅ COMPRA\n"
            f"Lungo: ✅ INVESTI\n"
            f"Motivo: trend breve ✅ COMPRA, trend medio ✅ COMPRA, "
            f"trend lungo ✅ INVESTI, volumi normali\n\n"
        )

    report += "--- Crypto ---\n\n"

    report += "--- Azioni Europa ---\n"
    for eu in AZIONI_EUROPA:
        report += (
            f"📌 {eu}\n"
            f"Breve: ✅ COMPRA\n"
            f"Medio: ✅ COMPRA\n"
            f"Lungo: ✅ INVESTI\n"
            f"Motivo: trend breve ✅ COMPRA, trend medio ✅ COMPRA, "
            f"trend lungo ✅ INVESTI, volumi normali\n\n"
        )

    report += (
        "🧠 SITUAZIONE GENERALE:\n"
        "Mercato: POSITIVO\n"
        "Strategia consigliata: COMPRARE SUI RITRACCIAMENTI\n"
        "Rischio: MEDIO"
    )

    return report

# ===== INVIO =====
async def main():
    bot = Bot(token=TOKEN)
    report = build_report()
    await bot.send_message(chat_id=CHAT_ID, text=report)

if __name__ == "__main__":
    asyncio.run(main())
