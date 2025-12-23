import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAZIONE BOT TELEGRAM ---
TOKEN = "8268985960:AAHqyZ679C4B4y7ICq96xQy5JU9PJ_1KiZg"
CHAT_ID = "595821281"

# Lista asset ampliata
ASSET = {
    "Azioni USA": ["NVDA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "TSLA", "NFLX", "JPM", "BAC"],
    "ETF": ["SPY", "QQQ", "VEA", "VGK", "IWV"],
    "Crypto": ["BTC-USD", "ETH-USD", "LTC-USD", "ADA-USD", "BNB-USD"],
    "Azioni Europa": ["ASML.AS", "SAP.DE", "LVMH.PA", "RDSA.AS", "SAN.MC"]
}

# Funzione per analizzare un asset
def analizza_asset(ticker):
    data = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
    if data.empty:
        return None
    close = data["Close"]
    volume = data["Volume"]

    # Medie mobili e volumi ultimi 50 giorni
    ma20 = float(close.rolling(window=20).mean().iloc[-1])
    ma50 = float(close.rolling(window=50).mean().iloc[-1])
    last = float(close.iloc[-1])
    vol50 = float(volume.rolling(window=50).mean().iloc[-1])
    vol_last = float(volume.iloc[-1])

    # Segnali
    breve = "⚠️ neutro"
    medio = "⚠️ attendere"
    lungo = "⚠️ attendere"

    if last > ma20:
        breve = "✅ COMPRA"
    if last > ma50:
        medio = "✅ COMPRA"
        lungo = "✅ INVESTI"
    elif last < ma50:
        medio = "❌ VENDI"
        lungo = "❌ VENDI"

    # Aggiunta controllo volumi (smart money)
    if vol_last > vol50:
        motivo = f"trend breve {breve}, trend medio {medio}, trend lungo {lungo}, volumi sopra la media"
    else:
        motivo = f"trend breve {breve}, trend medio {medio}, trend lungo {lungo}, volumi normali"

    return f"📌 {ticker}\nBreve: {breve}\nMedio: {medio}\nLungo: {lungo}\nMotivo: {motivo}\n"

# Funzione per inviare messaggio Telegram
def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": messaggio}
    requests.post(url, data=payload)

# --- CREAZIONE REPORT ---
report = f"📊 REPORT IA MERCATI – {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"

for categoria, tickers in ASSET.items():
    report += f"--- {categoria} ---\n"
    for t in tickers:
        res = analizza_asset(t)
        if res:
            report += res + "\n"

# Riepilogo generale
report += "\n🧠 SITUAZIONE GENERALE:\nMercato: POSITIVO\nStrategia consigliata: COMPRARE SUI RITRACCIAMENTI\nRischio: MEDIO"

# Invia report su Telegram
invia_telegram(report)
