import os
import requests
import yfinance as yf

def get_env(name):
    v = os.getenv(name)
    return v.strip() if v else ""

def main():
    TELEGRAM_TOKEN = get_env("TELEGRAM_TOKEN")
    CHAT_ID = get_env("CHAT_ID")

    ticker = "AAPL"

    try:
        data = yf.download(
            ticker,
            period="5d",
            interval="1d",
            progress=False,
            threads=False
        )

        if data.empty:
            text = f"⚠️ Nessun dato disponibile per {ticker}"
        else:
            last_price = round(float(data["Close"].dropna().iloc[-1]), 2)
            text = f"📈 {ticker} ultimo prezzo: {last_price}$"

    except Exception as e:
        text = f"❌ Errore nel recupero dati {ticker}"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    requests.post(url, data=payload, timeout=10)

if __name__ == "__main__":
    main()
