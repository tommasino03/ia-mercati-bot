import os
import yfinance as yf
import pandas as pd
from telegram import Bot

def get_env_variables():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")
    if not TELEGRAM_TOKEN or not CHAT_ID:
        raise ValueError("TELEGRAM_TOKEN o CHAT_ID mancanti nei Secrets")
    return TELEGRAM_TOKEN, CHAT_ID

def fetch_stock_data(ticker):
    data = yf.download(ticker, period="5d")
    return data

def send_message(bot, chat_id, text):
    bot.send_message(chat_id=chat_id, text=text)

def main():
    TELEGRAM_TOKEN, CHAT_ID = get_env_variables()
    bot = Bot(token=TELEGRAM_TOKEN)

    # Esempio di invio messaggio
    ticker = "AAPL"
    data = fetch_stock_data(ticker)
    last_close = data['Close'][-1]
    message = f"Ultimo prezzo di chiusura di {ticker}: {last_close}"
    send_message(bot, CHAT_ID, message)

if __name__ == "__main__":
    main()
