import os
import asyncio
from datetime import datetime
from telegram import Bot
import yfinance as yf

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print("TOKEN:", "OK" if TOKEN else "MANCANTE")
print("CHAT_ID:", "OK" if CHAT_ID else "MANCANTE")

SOGLIA = 2.0  # percentuale alert

def variazione_percentuale(ticker):
    df = yf.Ticker(ticker).history(period="2d")
    return round((df["Close"][-1] / df["Close"][-2] - 1) * 100, 2)

async def main():
    if not TOKEN or not CHAT_ID:
        raise ValueError("❌ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti")

    bot = Bot(token=TOKEN)

    try:
        risultati = {
            "₿ Bitcoin": variazione_percentuale("BTC-USD"),
            "📈 S&P 500": variazione_percentuale("^GSPC"),
            "💻 Nasdaq": variazione_percentuale("^IXIC"),
        }

        alert = {
            k: v for k, v in risultati.items() if abs(v) >= SOGLIA
        }

        if not alert:
            print("Nessun alert oggi")
            return  # SILENZIO TOTALE

        msg = "🚨 **ALERT MERCATI** 🚨\n\n"

        for nome, var in alert.items():
            simbolo = "⬆️" if var > 0 else "⬇️"
            msg += f"{nome}: {simbolo} {var}%\n"

        msg += f"\n🗓 {datetime.now().strftime('%d/%m/%Y')}"

        await bot.send_message(
            chat_id=int(CHAT_ID),
            text=msg
        )

    except Exception:
        # fallback ultra-sicuro: nessun messaggio, nessun crash
        print("Errore dati mercato, nessun alert inviato")

if __name__ == "__main__":
    asyncio.run(main())
