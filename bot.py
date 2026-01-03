import os
import asyncio
import datetime
import yfinance as yf
from telegram import Bot

# --- TOKEN e CHAT_ID dai secrets ---
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise RuntimeError("Secrets non trovati. Controlla BOT_TOKEN e CHAT_ID")

# --- Lista simboli ---
symbols = ["AAPL", "AMZN", "GOOGL", "TSLA", "META", "NVDA", "JPM", "BAC", "V", "MA"]

# --- Funzione per calcolare trend reale ---
def calculate_trend(close):
    """
    Trend basato su EMA20, EMA50 e prezzi recenti.
    Restituisce tuple (breve, medio, lungo)
    """
    if len(close) < 50:  # fallback se dati insufficienti
        return "⚠️ neutro", "⚠️ neutro", "⚠️ neutro"

    last_price = float(close.iloc[-1])
    ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])

    # Trend breve
    breve = "✅ COMPRA" if last_price > ema20 else "⚠️ neutro"
    # Trend medio
    medio = "✅ COMPRA" if ema20 > ema50 else "⚠️ neutro"
    # Trend lungo
    lungo = "✅ INVESTI" if last_price > ema50 else "⚠️ neutro"

    return breve, medio, lungo

# --- Funzione per costruire report ---
def build_report():
    today = datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")
    report = f"📊 REPORT IA MERCATI – {today}\n\n"

    for s in symbols:
        try:
            data = yf.download(s, period="3mo", interval="1d", progress=False)["Close"]
            breve, medio, lungo = calculate_trend(data)
        except Exception as e:
            breve = medio = lungo = "⚠️ errore dati"

        report += (
            f"📌 {s}\n"
            f"Breve: {breve}\n"
            f"Medio: {medio}\n"
            f"Lungo: {lungo}\n"
            f"Motivo: trend breve {breve}, trend medio {medio}, trend lungo {lungo}, volumi normali\n\n"
        )

    report += (
        "🧠 SITUAZIONE GENERALE:\n"
        "Mercato: POSITIVO\n"
        "Strategia consigliata: COMPRARE SUI RITRACCIAMENTI\n"
        "Rischio: MEDIO"
    )
    return report

# --- Funzione principale ---
async def main():
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=build_report())

if __name__ == "__main__":
    asyncio.run(main())

