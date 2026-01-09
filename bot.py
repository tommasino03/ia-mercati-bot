import os
import datetime
import asyncio
from telegram import Bot

# =====================================================
# LETTURA ULTRA-ROBUSTA DEI SECRETS
# =====================================================
def get_env():
    possibili_token = [
        "TELEGRAM_TOKEN",
        "BOT_TOKEN",
        "telegram_token",
        "bot_token"
    ]

    possibili_chat = [
        "CHAT_ID",
        "TELEGRAM_CHAT_ID",
        "chat_id"
    ]

    token = ""
    chat_id = ""

    for k in possibili_token:
        if os.environ.get(k):
            token = os.environ.get(k).strip()

    for k in possibili_chat:
        if os.environ.get(k):
            chat_id = os.environ.get(k).strip()

    return token, chat_id


# =====================================================
# REPORT
# =====================================================
def genera_report():
    ora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""📊 REPORT IA MERCATI – {ora}

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


# =====================================================
# MAIN ASYNC (NON SI BLOCCA MAI)
# =====================================================
async def main():
    token, chat_id = get_env()

    if not token or not chat_id:
        print("⚠️ Token o Chat ID non trovati nei Secrets")
        return

    bot = Bot(token=token)
    messaggio = genera_report()

    await bot.send_message(chat_id=chat_id, text=messaggio)
    print("✅ Messaggio Telegram inviato")


# =====================================================
# AVVIO
# =====================================================
if __name__ == "__main__":
    asyncio.run(main())
