import os
import asyncio
from datetime import datetime
from telegram import Bot


async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token or not chat_id:
        raise ValueError("Token o Chat ID mancanti")

    bot = Bot(token=token)

    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Dati simulati (placeholder sicuro)
    markets = {
        "S&P 500": "+0.42%",
        "NASDAQ": "-0.18%",
        "BTC": "+1.25%",
        "ETH": "+0.67%"
    }

    market_text = "\n".join([f"• {k}: {v}" for k, v in markets.items()])

    message = (
        "📊 **Aggiornamento Mercati**\n\n"
        f"🕒 {now}\n\n"
        f"{market_text}\n\n"
        "✅ Bot stabile\n"
        "🚀 Pronto per automazioni"
    )

    await bot.send_message(chat_id=chat_id, text=message)


if __name__ == "__main__":
    asyncio.run(main())
