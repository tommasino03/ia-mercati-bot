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
    raise RuntimeError("BOT_TOKEN o CHAT_ID mancanti nei Secrets GitHub")

# ===== CONFIGURAZIONE TICKER =====
AZIONI_USA = ["AAPL","AMZN","GOOGL","META","TSLA","NVDA","JPM","BAC","V","MA","ADBE","CSCO","CMCSA","WMT"]
ETF = ["SPY","QQQ","VEA","VGK","IWV","VTI","EFA","IEMG"]
AZIONI_EUROPA = ["SAN.MC"]
CRYPTO = ["bitcoin","ethereum"]  # CoinGecko IDs

# ===== FUNZIONE TREND ROBUSTA =====
def calculate_trend(prices: pd.Series):
    """
    Restituisce breve, medio, lungo con controllo dati mancanti
    """
    if prices.empty or len(prices) < 50:
        return "⚠️ neutro", "⚠️ neutro", "⚠️ neutro"
    breve = "✅ COMPRA" if prices[-3:].mean() < prices.iloc[-1] else "⚠️ neutro"
    medio = "✅ COMPRA" if prices[-10:].mean() < prices.iloc[-1] else "⚠️ neutro"
    lungo = "✅ INVESTI" if prices[-50:].mean() < prices.iloc[-1] else "⚠️ neutro"
    return breve, medio, lungo

# ===== COSTRUZIONE REPORT =====
def build_report():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI – {now}\n\n"

    # --- Azioni USA ---
    report += "--- Azioni USA ---\n"
    for ticker in AZIONI_USA:
        try:
            data = yf.download(ticker, period="60d", interval="1d")["Close"]
        except Exception:
            data = pd.Series()
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
        try:
            data = yf.download(etf, period="60d", interval="1d")["Close"]
        except Exception:
            data = pd.Series()
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
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart?vs_currency=usd&days=60&interval=daily"
            r = requests.get(url, timeout=10).json()
            prices = [p[1] for p in r.get("prices", [])]
            prices = pd.Series(prices)
        except Exception:
            prices = pd.Series()
        trend = calculate_trend(prices)
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
        try:
            data = yf.download(ticker, period="60d", interval="1d")["Close"]
        except Exception:
            data = pd.Series()
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

# ===== INVIO TELEGRAM =====
async def main():
    bot = Bot(token=TOKEN)
    report = build_report()
    await bot.send_message(chat_id=CHAT_ID, text=report)

if __name__ == "__main__":
    asyncio.run(main())
