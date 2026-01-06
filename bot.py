import os
import requests
from telegram import Bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("TELEGRAM_TOKEN o CHAT_ID mancanti nei Secrets")

def get_price(symbol: str) -> float | None:
    """
    Recupera il prezzo attuale da Yahoo Finance (API pubblica, senza librerie)
    """
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    r = requests.get(url, timeout=10)
    data = r.json()

    try:
        return float(data["quoteResponse"]["result"][0]["regularMarketPrice"])
    except Exception:
        return None

def build_report() -> str:
    assets = {
        "BTC-USD": "Bitcoin",
        "ETH-USD": "Ethereum",
        "AAPL": "Apple",
        "MSFT": "Microsoft"
    }

    report = "📊 *Report Mercati*\n\n"

    for symbol, name in assets.items():
        price = get_price(symbol)
        if price is None:
            report += f"❌ {name}: dati non disponibili\n"
        else:
            report += f"✅ {name}: {price:.2f}\n"

    return report

def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    message = build_report()
    bot.send_message(chat_id=CHAT_ID, text=message)

if __name__ == "__main__":
    main()
