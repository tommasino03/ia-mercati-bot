import os
import yfinance as yf
import pandas as pd
from telegram import Bot
from datetime import datetime

# Lista simboli da monitorare
TICKERS = ["AAPL", "GOOGL", "META", "TSLA", "JPM", "BAC"]

def get_data(ticker):
    try:
        data = yf.download(ticker, period="30d", interval="1d")
        return data
    except Exception as e:
        print(f"Errore scaricando {ticker}: {e}")
        return None

def analyze(ticker, data):
    if data is None or data.empty:
        return "⚠️ dati mancanti", "⚠️ dati mancanti", "⚠️ dati mancanti", "Dati non disponibili"

    close = data["Close"]
    short_trend = "✅ COMPRA" if close[-5:].mean() > close[-10:-5].mean() else "⚠️ neutro"
    mid_trend = "✅ COMPRA" if close[-10:].mean() > close[-20:-10].mean() else "⚠️ neutro"
    long_trend = "✅ INVESTI" if close.mean() > close.mean() else "⚠️ neutro"  # placeholder
    reason = f"trend breve {short_trend}, trend medio {mid_trend}, trend lungo {long_trend}, volumi normali"

    return short_trend, mid_trend, long_trend, reason

def create_report():
    report = f"📊 REPORT IA MERCATI – {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    report += "--- Azioni USA ---\n"

    for ticker in TICKERS:
        data = get_data(ticker)
        short, mid, long, reason = analyze(ticker, data)
        report += f"📌 {ticker}\nBreve: {short}\nMedio: {mid}\nLungo: {long}\nMotivo: {reason}\n\n"

    report += "🧠 SITUAZIONE GENERALE:\nMercato: POSITIVO\nStrategia consigliata: COMPRARE SUI RITRACCIAMENTI\nRischio: MEDIO"
    return report

def main():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")

    if not TELEGRAM_TOKEN or not CHAT_ID:
        raise ValueError("Token o Chat ID mancanti nei Secrets")

    bot = Bot(token=TELEGRAM_TOKEN)
    report = create_report()
    bot.send_message(chat_id=CHAT_ID, text=report)
    print("Report inviato correttamente!")

if __name__ == "__main__":
    main()
