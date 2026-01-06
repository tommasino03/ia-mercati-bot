import os
import logging
from telegram import Bot
from telegram.error import TelegramError
import yfinance as yf
import pandas as pd

# Logging base
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def get_env_variables():
    # Legge TELEGRAM_TOKEN e CHAT_ID dai secrets GitHub Actions
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    CHAT_ID = os.environ.get("CHAT_ID")

    # Pulizia degli spazi se presenti
    TELEGRAM_TOKEN = TELEGRAM_TOKEN.strip() if TELEGRAM_TOKEN else None
    CHAT_ID = CHAT_ID.strip() if CHAT_ID else None

    if not TELEGRAM_TOKEN or not CHAT_ID:
        raise ValueError("TELEGRAM_TOKEN o CHAT_ID mancanti nei Secrets")
    return TELEGRAM_TOKEN, CHAT_ID

def send_message(bot, chat_id, text):
    try:
        bot.send_message(chat_id=chat_id, text=text)
        logging.info("Messaggio inviato correttamente")
    except TelegramError as e:
        logging.error(f"Errore invio messaggio: {e}")

def get_stock_info(ticker):
    data = yf.Ticker(ticker)
    hist = data.history(period="5d")
    last_close = hist['Close'][-1]
    return last_close

def main():
    TELEGRAM_TOKEN, CHAT_ID = get_env_variables()
    bot = Bot(token=TELEGRAM_TOKEN)

    # Esempio di messaggio
    ticker = "AAPL"
    last_price = get_stock_info(ticker)
    message = f"Ultimo prezzo di {ticker}: {last_price}"
    send_message(bot, CHAT_ID, message)

if __name__ == "__main__":
    main()
