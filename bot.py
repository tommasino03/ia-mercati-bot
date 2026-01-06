import os
import requests
from telegram import Bot

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

# =========================
# FUNZIONI
# =========================
def get_price(symbol):
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    r = requests.get(url, timeout=10)
    data = r.json()

    result = data["quoteResponse"]["result"]
    if not result:
        return None

    price = result[0].get("regularMarketPrice")
    change = result[0].get("regularMarketChangePercent")

    return price, change


def main():
    bot = Bot(token=TELEGRAM_TOKEN)

    messages = []
    for symbol in SYMBOLS:
        data = get_price(symbol)
        if not data:
            continue

        price, change = data

        # Condizione semplice (step 2 automatico)
        if change is not None and abs(change) >= 1:
            messages.append(
                f"📊 {symbol}\n"
                f"💰 Prezzo: {price}\n"
                f"📈 Variazione: {round(change, 2)}%\n"
            )

    if messages:
        final_message = "📢 **Segnali di mercato**\n\n" + "\n".join(messages)
        bot.send_message(chat_id=CHAT_ID, text=final_message)
    else:
        print("Nessun segnale rilevante oggi.")


if __name__ == "__main__":
    main()
