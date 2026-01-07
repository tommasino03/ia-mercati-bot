import os
from telegram import Bot
from telegram.error import TelegramError

token = os.environ.get("TELEGRAM_TOKEN")
chat_id = os.environ.get("CHAT_ID")

if not token or not chat_id:
    raise ValueError("TELEGRAM_TOKEN o CHAT_ID mancanti nei Secrets")

bot = Bot(token=token)

try:
    me = bot.get_me()
    print(f"Bot funzionante: {me.username}")
    bot.send_message(chat_id=chat_id, text="✅ Test messaggio arrivato!")
    print("Messaggio inviato correttamente!")
except TelegramError as e:
    print("Errore Telegram:", e)
