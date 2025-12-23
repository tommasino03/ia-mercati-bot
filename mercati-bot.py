import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
import json

# --- CONFIGURAZIONE BOT TELEGRAM ---
TOKEN = "8268985960:AAHqyZ679C4B4y7ICq96xQy5JU9PJ_1KiZg"
CHAT_ID = "595821281"

ASSET = {
    "Azioni USA": ["AAPL","MSFT","AMZN","GOOGL","META","TSLA","NVDA","NFLX","JPM","BAC"],
    "ETF": ["SPY","QQQ","VEA","VGK","IWV"],
    "Crypto": ["BTC-USD","ETH-USD","LTC-USD","ADA-USD","BNB-USD"],
    "Azioni Europa": ["ASML.AS","SAP.DE","LVMH.PA","RDSA.AS","SAN.MC"]
}

def analizza_asset(ticker):
    data = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
    if data.empty:
        return None
    close = data["Close"]
    volume = data["Volume"]
    ma20 = float(close.rolling(window=20).mean().iloc[-1])
    ma50 = float(close.rolling(window=50).mean().iloc[-1])
    last = float(close.iloc[-1])
    vol50 = float(volume.rolling(window=50).mean().iloc[-1])
    vol_last = float(volume.iloc[-1])
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
    forte = vol_last > vol50
    mostra = False
    if (breve == "✅ COMPRA" and forte) or (medio == "❌ VENDI" and forte) or lungo == "✅ INVESTI":
        mostra = True
    motivo = f"trend breve {breve}, trend medio {medio}, trend lungo {lungo}, volumi {'sopra la media' if forte else 'normali'}"
    if mostra:
        return {"ticker": ticker, "breve": breve, "medio": medio, "lungo": lungo, "motivo": motivo}
    else:
        return None

def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": messaggio}
    requests.post(url, data=payload)

# --- CREAZIONE REPORT ---
report_testo = f"📊 REPORT IA MERCATI – {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
report_json = []

for categoria, tickers in ASSET.items():
    report_testo += f"--- {categoria} ---\n"
    for t in tickers:
        res = analizza_asset(t)
        if res:
            report_json.append(res)
            report_testo += f"📌 {res['ticker']}\nBreve: {res['breve']}\nMedio: {res['medio']}\nLungo: {res['lungo']}\nMotivo: {res['motivo']}\n\n"

report_testo += "\n🧠 SITUAZIONE GENERALE:\nMercato: POSITIVO\nStrategia consigliata: COMPRARE SUI RITRACCIAMENTI\nRischio: MEDIO"

# salva anche JSON per app
with open("signals.json", "w") as f:
    json.dump(report_json, f, indent=4)

# invia report Telegram
invia_telegram(report_testo)
