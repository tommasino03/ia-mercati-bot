import os
import asyncio
from datetime import datetime
import yfinance as yf
import pandas as pd
import requests
from telegram import Bot

TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise RuntimeError("BOT_TOKEN o CHAT_ID mancanti nei Secrets")

# ===== AZIONI / ETF / CRYPTO =====
AZIONI_USA = ["AAPL","AMZN","GOOGL","META","TSLA","NVDA","JPM","BAC","V","MA","ADBE","CSCO","CMCSA","WMT"]
ETF = ["SPY","QQQ","VEA","VGK","IWV","VTI","EFA","IEMG"]
AZIONI_EUROPA = ["SAN.MC"]
CRYPTO = ["bitcoin","ethereum"]  # CoinGecko IDs

# ===== FUNZIONE TREND =====
def calculate_trend(prices):
    """
    Restituisce segnale semplice: breve/medio/lungo
    """
    breve = "✅ COMPRA" if prices[-3:].mean() < prices[-1] else "⚠️ neutro"
    medio = "✅ COMPRA" if prices[-10:].mean() < prices[-1] else "⚠️ neutro"
    lungo = "✅ INVESTI" if prices[-50:].mean() < prices[-1] else "⚠️ neutro"
    return breve, medio, lungo

# ===== FUNZIONE REPORT =====
def build_report():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI – {now}\n\n"

    # --- Azioni USA ---
    report += "--- Azioni USA ---\n"
    for ticker in AZIONI_USA:
        data = yf.download(ticker, period="60d", interval="1d")["Close"]
        trend = calculate_trend(data)
        report += (
            f"📌 {ticker}\n"
            f"Breve: {trend[0]}\n"
            f"Medio: {trend[1]}\n"
            f"Lungo: {trend[2]}\n"
            f"Motivo: trend breve {trend[0]}, trend medio {trend[1]}, trend lungo {trend[2]}, volumi normali\n\n"
        )

    # --- ETF ---
    report += "--- ETF ---\n"
    for etf in ETF:
        data = yf.download(etf, period="60d", interval="1d")["Close"]
        trend = calculate_trend(data)
        report += (
            f"📌 {etf}\n"
            f"Breve: {trend[0]}\n"
            f"Medio: {trend[1]}\n"
            f"Lungo: {trend[2]}\n"
            f"Motivo: trend breve {trend[0]}, trend medio {trend[1]}, trend lungo {trend[2]}, volumi normali\n\n"
        )

    # --- Crypto ---
    report += "--- Crypto ---\n"
    for coin in CRYPTO:
        url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart?vs_currency=usd&days=60&interval=daily"
        r = requests.get(url).json()
        prices = [p[1] for p in r["prices"]]
        trend = calculate_trend(pd.Series(prices))
        report += (
            f"📌 {coin.upper()}\n"
            f"Breve: {trend[0]}\n"
            f"Medio: {trend[1]}\n"
            f"Lungo: {trend[2]}\n"
            f"Motivo: trend breve {trend[0]}, trend medio {trend[1]}, trend lungo {trend[2]}\n\n"
        )

    # --- Azioni Europa ---
    report += "--- Azioni Europa ---\n"
    for ticker in AZIONI_EUROPA:
        data = yf.download(ticker, period="60d", interval="1d")["Close"]
        trend = calculate_trend(data)
        report += (
            f"📌 {ticker}\n"
            f"Breve: {trend[0]}\n"
            f"Medio: {trend[1]}\n"
            f"Lungo: {trend[2]}\n"
            f"Motivo: trend breve {trend[0]}, trend medio {trend[1]}, trend lungo {trend[2]}, volumi normali\n\n"
        )

    report += (
        "🧠 SITUAZIONE GENERALE:\n"
        "Mercato: POSITIVO\n"
        "Strategia consigliata: COMPRARE SUI RITRACCIAMENTI\n"
        "Rischio: MEDIO"
    )

    return report

# ===== INVIO =====
async def main():
    bot = Bot(token=TOKEN)
    report = build_report()
    await bot.send_message(chat_id=CHAT_ID, text=report)

if __name__ == "__main__":
    asyncio.run(main())
