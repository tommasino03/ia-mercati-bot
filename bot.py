import os
import asyncio
from datetime import datetime
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def build_report():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    report = f"""📊 REPORT IA MERCATI – {now}

--- Azioni USA ---
📌 AAPL
Breve: ✅ COMPRA
Medio: ✅ COMPRA
Lungo: ✅ INVESTI

📌 AMZN
Breve: ✅ COMPRA
Medio: ✅ COMPRA
Lungo: ✅ INVESTI

📌 GOOGL
Breve: ⚠️ neutro
Medio: ✅ COMPRA
Lungo: ✅ INVESTI

--- ETF ---
📌 SPY
Breve: ✅ COMPRA
Medio: ✅ COMPRA
Lungo: ✅ INVESTI

📌 QQQ
Breve: ✅ COMPRA
Medio: ✅ COMPRA
Lungo: ✅ INVESTI

--- Azioni Europa ---
📌 SAN.MC
Breve: ⚠️ neutro
Medio: ✅ COMPRA
Lungo: ✅ INVESTI

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
