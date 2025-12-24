# bot.py
import os
from telegram import Bot
from ia_mercati import calcola_segnali

# --- CONFIGURAZIONE ---
TOKEN = "8268985960:AAHqyZ679C4B4y7ICq96xQy5JU9PJ_1KiZg"  # sostituisci con il token del tuo bot Telegram
CHAT_ID = "595821281"      # sostituisci con il tuo chat ID
assets = ["AAPL", "SPY", "NVDA", "BTC-USD"]  # asset da monitorare

# --- CREA OGGETTO BOT ---
bot = Bot(token=TOKEN)

# --- CALCOLO SEGNALI ---
segnali = calcola_segnali(assets)

# --- INVIO MESSAGGI TELEGRAM ---
for asset, info in segnali.items():
    messaggio = (
        f"📊 {asset}\n"
        f"Score: {info['score']}\n"
        f"Azione: {info['azione']}\n"
        f"Confidence: {info['confidence']*100}%"
    )
    bot.send_message(chat_id=CHAT_ID, text=messaggio)

print("Messaggi inviati con successo!")
