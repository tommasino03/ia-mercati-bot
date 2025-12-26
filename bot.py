# bot.py
import os
from telegram import Bot
from ia_mercati import calcola_segnali

# --- CONFIGURAZIONE ---
TOKEN = os.getenv("8268985960:AAHqyZ679C4B4y7ICq96xQy5JU9PJ_1KiZg")
CHAT_ID = os.getenv("595821281")

assets = ["AAPL", "SPY", "NVDA", "BTC-USD"]

# --- CREA BOT ---
bot = Bot(token=TOKEN)

# --- CALCOLO SEGNALI ---
segnali = calcola_segnali(assets)

# --- INVIO MESSAGGI ---
for asset, info in segnali.items():
    messaggio = (
        f"📊 {asset}\n"
        f"Score: {info['score']}\n"
        f"Azione: {info['azione']}\n"
        f"Confidence: {int(info['confidence'] * 100)}%"
    )

    bot.send_message(chat_id=CHAT_ID, text=messaggio)

print("✅ Messaggi Telegram inviati correttamente")
