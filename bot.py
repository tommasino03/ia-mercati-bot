import os
import asyncio
from datetime import datetime
from telegram import Bot

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print("TOKEN:", "OK" if TOKEN else "MANCANTE")
print("CHAT_ID:", "OK" if CHAT_ID else "MANCANTE")

MESSAGGI = [
    "📈 Buongiorno! Ricorda: la costanza batte il talento.",
    "💰 Oggi controlla le spese inutili: piccoli tagli = grandi risultati.",
    "🧠 Investire in conoscenza paga sempre i migliori interessi.",
    "⏳ Il tempo nel mercato conta più del timing del mercato.",
    "🚀 Un passo al giorno ti porta più lontano di quanto pensi.",
    "📊 Disciplina > emozioni. Sempre.",
    "🔁 Automatizza ciò che puoi, semplifica il resto."
]

async def main():
    if not TOKEN or not CHAT_ID:
        raise ValueError("❌ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti")

    bot = Bot(token=TOKEN)

    # Usa il giorno dell'anno per scegliere il messaggio
    giorno = datetime.now().timetuple().tm_yday
    messaggio = MESSAGGI[giorno % len(MESSAGGI)]

    await bot.send_message(
        chat_id=int(CHAT_ID),
        text=messaggio
    )

if __name__ == "__main__":
    asyncio.run(main())
