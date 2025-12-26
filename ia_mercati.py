# ia_mercati.py
import yfinance as yf
import pandas as pd

def calcola_segnali(asset_list, periodo=50):
    """
    asset_list: lista di simboli es. ["AAPL", "SPY", "NVDA", "BTC-USD"]
    periodo: numero di giorni per la media mobile e il volume medio
    ritorna: dict con segnali {"ASSET": {"score": int, "azione": str, "confidence": float}}
    """
    segnali = {}

    for asset in asset_list:
        # Scarica dati ultimi 6 mesi
        data = yf.download(asset, period="6mo", interval="1d", progress=False)

        if data.empty:
            segnali[asset] = {"score": 0, "azione": "ATTENDI", "confidence": 0}
            continue

        # Prezzo di chiusura e volumi
        close = data["Close"]
        vol = data["Volume"]

        # Medie mobili
        ma20 = close[-20:].mean()
        ma50 = close[-50:].mean()

        # Volume medio 50 giorni
        vol50 = vol[-50:].mean()

        # Score basato su trend e volume
        score = 0
        if close.iloc[-1] > ma50:
            score += 2
        if close.iloc[-1] > ma20:
            score += 2
        if vol.iloc[-1] > vol50:
            score += 1

        # Determina azione
        if score >= 4:
            azione = "COMPRA"
        elif score >= 2:
            azione = "ATTENDI"
        else:
            azione = "VENDI"

        # Confidence proporzionale allo score
        confidence = score / 5

        segnali[asset] = {"score": score, "azione": azione, "confidence": round(confidence, 2)}

    return segnali

# Esempio di utilizzo:
if __name__ == "__main__":
    assets = ["AAPL", "SPY", "NVDA", "BTC-USD"]
    segnali = calcola_segnali(assets)
    for a, info in segnali.items():
        print(f"{a}: {info}")
