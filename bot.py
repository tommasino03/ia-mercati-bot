import os
import datetime
import asyncio

from telegram import Bot

# =========================================================
# LETTURA SICURA DEI SECRETS (ANTI-ERRORI)
# =========================================================
def get_env():
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    chat_id = os.environ.get("CHAT_ID", "").strip()

    if not token or not chat_id:
        raise ValueError("Token o Chat ID mancanti")

    return token, chat_id


# =========================================================
# GENERAZIONE REPORT (SENZA LIBRERIE ESTERNE)
# =========================================================
def genera_report():
    oggi = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

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


# =========================================================
# MAIN ASINCRONO (CORRETTO PER python-telegram-bot v20+)
# =========================================================
async def main():
    token, chat_id = get_env()
    bot = Bot(token=token)

    messaggio = genera_report()

    await bot.send_message(
        chat_id=chat_id,
        text=messaggio
    )

    print("✅ Messaggio Telegram inviato con successo")


# =========================================================
# AVVIO
# =========================================================
if __name__ == "__main__":
    asyncio.run(main())
