import os
import asyncio
import yfinance as yf
from telegram import Bot

async def main():
    # Legge i Secrets (GIÀ PRESENTI)
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")

    if not TELEGRAM_TOKEN or not CHAT_ID:
        raise ValueError("Token o Chat ID mancanti")

    bot = Bot(token=TELEGRAM_TOKEN)

    # Scarica dati AAPL (sicuro e stabile)
    ticker = yf.Ticker("AAPL")
    data = ticker.history(period="1d")

    if data.empty:
        await bot.send_message(
            chat_id=CHAT_ID,
            text="⚠️ Nessun dato disponibile per AAPL"
        )
        return

    prezzo = round(float(data["Close"].iloc[-1]), 2)

    messaggio = f"📈 Prezzo attuale AAPL: ${prezzo}"

    await bot.send_message(chat_id=CHAT_ID, text=messaggio)

if __name__ == "__main__":
    asyncio.run(main())
