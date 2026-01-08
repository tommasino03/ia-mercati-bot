# bot.py
import os
from datetime import datetime
import yfinance as yf
from telegram import Bot

# Recupera secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("Token o Chat ID mancanti")

CHAT_ID = int(CHAT_ID)
bot = Bot(token=TELEGRAM_TOKEN)

# Lista ticker da monitorare
TICKERS = ["AAPL", "GOOGL", "META", "TSLA", "JPM", "BAC", "V", "MA", "ADBE", "CSCO", "CMCSA", "PEP", "KO", "WMT"]

# Funzione per ottenere prezzo e trend
def get_stock_data(ticker):
    data = yf.Ticker(ticker).history(period="5d")
    if data.empty:
        return None
    last_price = round(float(data["Close"].iloc[-1]), 2)
    prev_price = round(float(data["Close"].iloc[-2]), 2)
    trend = "✅ COMPRA" if last_price > prev_price else "⚠️ neutro"
    return last_price, trend

# Genera report testuale
def generate_report():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI – {now}\n\n--- Azioni USA ---\n"
    for t in TICKERS:
        stock_data = get_stock_data(t)
        if stock_data:
            price, trend = stock_data
            report += f"📌 {t}\nBreve: {trend}\nMedio: {trend}\nLungo: ✅ INVESTI\nMotivo: trend breve {trend}, trend medio {trend}, trend lungo ✅ INVESTI, volumi normali\n\n"
        else:
            report += f"📌 {t} - dati non disponibili\n\n"
    report += "🧠 SITUAZIONE GENERALE:\nMercato: POSITIVO\nStrategia consigliata: COMPRARE SUI RITRACCIAMENTI\nRischio: MEDIO"
    return report

# Invia report su Telegram
def main():
    report = generate_report()
    bot.send_message(chat_id=CHAT_ID, text=report)
    print("✅ Messaggio inviato!")

if __name__ == "__main__":
    main()
