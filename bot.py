import os
import requests

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token or not chat_id:
        raise ValueError("Token o Chat ID mancanti")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": "✅ Bot operativo. Messaggio di test riuscito."
    }

    response = requests.post(url, data=payload)

    if response.status_code != 200:
        raise Exception(f"Errore Telegram: {response.text}")

if __name__ == "__main__":
    main()
