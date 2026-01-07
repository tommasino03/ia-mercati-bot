import os
import requests
import yfinance as yf

def get_env(name):
    v = os.getenv(name)
    return v.strip() if v else ""

def main():
    TELEGRAM_TOKEN = get_env("TELEGRAM_TOKEN")
    CHAT_ID = get_env("CHAT_ID")

    # dati mercato
    data = yf.download("AAPL", period="5d", progress=False)
    last_price = round(float(data["Close"].iloc[-1]), 2)

    text = f"📈 AAPL ultimo prezzo: {last_price}$"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    # invio messaggio (nessun crash possibile)
    requests.post(url, data=payload)

if __name__ == "__main__":
    main()
