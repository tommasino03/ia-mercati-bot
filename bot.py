from telegram import Bot
from datetime import datetime
import asyncio
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def genera_report():
    oggi = datetime.now().strftime("%d/%m/%Y %H:%M")

    report = f"""📊 REPORT IA MERCATI – {oggi}

--- Azioni USA ---
📌 AAPL
Breve: ⚠️ neutro
Medio: ✅ COMPRA
Lungo: ✅ INVESTI

📌 GOOGL
Breve: ⚠️ neutro
Medio: ✅ COMPRA
Lungo: ✅ INVESTI

📌 META
Breve: ✅ COMPRA
Medio: ✅ COMPRA
Lungo: ✅ INVESTI

📌 TSLA
Breve: ✅ COMPRA
Medio: ✅ COMPRA
Lungo: ✅ INVESTI

📌 JPM
Breve: ✅ COMPRA
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
Breve: ✅ COMPRA
Medio: ✅ COMPRA
Lungo: ✅ INVESTI

🧠 SITUAZIONE GENERALE:
Mercato: POSITIVO
Strategia consigliata: COMPRARE SUI RITRACCIAMENTI
Rischio: MEDIO
"""

    return report

async def main():
    bot = Bot(token=TOKEN)
    messaggio = genera_report()
    await bot.send_message(chat_id=CHAT_ID, text=messaggio)

if __name__ == "__main__":
    asyncio.run(main())
