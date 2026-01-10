import os
import asyncio
from datetime import datetime
from telegram import Bot

import yfinance as yf

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print("TOKEN:", "OK" if TOKEN else "MANCANTE")
print("CHAT_ID:", "OK" if CHAT_ID else "MANCANTE")

async def main():
    if not TOKEN or not CHAT_ID:
        raise ValueError("❌ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti")

    bot = Bot(token=TOKEN)

    try:
        btc = yf.Ticker("BTC-USD").history(period="2d")
        sp = yf.Ticker("^GSPC").history(period="2d")
        nasdaq = yf.Ticker("^IXIC").history(period="2d")

        def variazione(df):
            return round((df["Close"][-1] / df["Close"][-2] - 1) * 100, 2)

        msg = (
            "📊 **Mercati – aggiornamento giornaliero**\n\n"
            f"₿ Bitcoin: {variazione(btc)}%\n"
            f"📈 S&P 500: {variazione(sp)}%\n"
            f"💻 Nasdaq: {variazione(nasdaq)}%\n\n"
            f"🗓 {datetime.now().strftime('%d/%m/%Y')}"
        )

    except Exception as e:
        # FALLBACK SICURO → NIENTE CRASH
        msg = (
            "⚠️ Aggiornamento mercati non disponibile oggi.\n\n"
            "📌 Nessuna azione richiesta.\n"
            "Il bot riproverà automaticamente domani."
        )

    await bot.send_message(
        chat_id=int(CHAT_ID),
        text=msg
    )

if __name__ == "__main__":
    asyncio.run(main())
