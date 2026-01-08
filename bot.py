import os
import asyncio
from datetime import datetime
from telegram import Bot


# soglie alert (modificabili in futuro)
BTC_PRICE = 43500
BTC_ALERT = 43000


async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token or not chat_id:
        raise ValueError("Token o Chat ID mancanti")

    bot = Bot(token=token)

    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    message = (
        "🚨 **ALERT MERCATO**\n\n"
        f"🕒 {now}\n\n"
        f"₿ BTC attuale: ${BTC_PRICE}\n"
        f"🎯 Soglia alert: ${BTC_ALERT}\n\n"
    )

    if BTC_PRICE > BTC_ALERT:
        message += "✅ **Condizione raggiunta! BTC sopra la soglia** 🚀"
    else:
        message += "⏳ BTC sotto la soglia, nessuna azione."

    await bot.send_message(chat_id=chat_id, text=message)


if __name__ == "__main__":
    asyncio.run(main())
