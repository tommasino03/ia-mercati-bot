# bot.py
import os
import time
import yfinance as yf
from telegram import Bot

# --- VARIABILI DA RENDER (NON SCRITTE NEL CODICE) ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

assets = {
    "AAPL": "Apple",
    "SPY": "S&P500",
    "NVDA": "NVIDIA",
    "BTC-USD": "Bitcoin"
}

def calcola_score(ticker):
    data = yf.download(ticker, period="7d", interval="1d", progress=False)

    if len(data) < 2:
        return 0

    chiusura_oggi = data["Close"].iloc[-1]
    chiusura_ieri = data["Close"].iloc[-2]

    variazione = (chiusura_oggi - chiusura_ieri) / chiusura_ieri

    if variazione > 0.02:
        return 7
    elif variazione > 0:
        return 5
    elif variazione > -0.02:
        return 3
    else:
        return 1

def invia_segnali():
    messaggio_finale = "📊 Segnali Mercati\n\n"

    for ticker, nome in assets.items():
        score = calcola_score(ticker)

        if score >= 6:
            azione = "COMPRA"
        elif score >= 4:
            azione = "ATTENDI"
        else:
            azione = "NON ENTRARE"

        messaggio_finale += (
            f"{nome}\n"
            f"Score: {score}\n"
            f"Azione: {azione}\n\n"
        )

    bot.send_message(chat_id=CHAT_ID, text=messaggio_finale)

# --- LOOP INFINITO (SERVE A RENDER) ---
while True:
    invia_segnali()
    print("Segnali inviati. Attendo 24 ore.")
    time.sleep(86400)  # 24 ore
