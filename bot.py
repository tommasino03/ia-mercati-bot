# bot.py
import requests
from ia_mercati import calcola_segnali

# --- CONFIG ---
TOKEN = "8268985960:AAHqyZ679C4B4y7ICq96xQy5JU9PJ_1KiZg"
CHAT_ID = "595821281"

assets = ["AAPL", "SPY", "NVDA", "BTC-USD"]

# --- FUNZIONE INVIO TELEGRAM ---
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, data=payload)

# --- CALCOLO SEGNALI ---
segnali = calcola_segnali(assets)

# --- INVIO MESSAGGI ---
for asset, info in segnali.items():
    messaggio = (
        f"📊 {asset}\n"
        f"Score: {info['score']}\n"
        f"Azione: {info['azione']}\n"
        f"Confidence: {int(info['confidence']*100)}%\n"
        f"Motivi: {', '.join(info['motivi'])}"
    )
    send_telegram_message(messaggio)

print("Messaggi Telegram inviati con successo")
