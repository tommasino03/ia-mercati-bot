# ia_mercati.py
import yfinance as yf
import pandas as pd

def calcola_segnali(assets):
    risultati = {}

    for asset in assets:
        try:
            df = yf.download(asset, period="6mo", interval="1d")

            if df.empty:
                continue

            close = df["Close"]

            # Medie mobili
            ma20 = close.rolling(window=20).mean()
            ma50 = close.rolling(window=50).mean()

            # Valori attuali (ULTIMO GIORNO)
            prezzo_attuale = close.iloc[-1]
            ma20_attuale = ma20.iloc[-1]
            ma50_attuale = ma50.iloc[-1]

            score = 0

            # Logica score (semplice ma corretta)
            if prezzo_attuale > ma20_attuale:
                score += 1
            if prezzo_attuale > ma50_attuale:
                score += 1
            if ma20_attuale > ma50_attuale:
                score += 1

            # Decisione
            if score >= 2:
                azione = "COMPRA"
                confidence = 0.7
            else:
                azione = "ATTENDI"
                confidence = 0.4

            risultati[asset] = {
                "score": score,
                "azione": azione,
                "confidence": confidence
            }

        except Exception as e:
            risultati[asset] = {
                "score": 0,
                "azione": "ERRORE",
                "confidence": 0,
                "errore": str(e)
            }

    return risultati
