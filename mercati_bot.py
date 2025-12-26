# ia_mercati.py
import yfinance as yf
import json
from datetime import datetime

def calcola_segnali(assets, file_storico="signals.json"):
    risultati = {}

    for asset in assets:
        try:
            data = yf.download(asset, period="6mo", interval="1d", progress=False)

            close = data["Close"]
            volume = data["Volume"]

            # --- INDICATORI ---
            ma20 = close.rolling(20).mean()
            ma50 = close.rolling(50).mean()

            last_price = float(close.iloc[-1])
            last_ma20 = float(ma20.iloc[-1])
            last_ma50 = float(ma50.iloc[-1])

            last_volume = float(volume.iloc[-1])
            avg_volume = float(volume.rolling(20).mean().iloc[-1])

            score = 0
            motivi = []

            # TREND
            if last_price > last_ma50:
                score += 2
                motivi.append("Prezzo sopra MA50 (trend rialzista)")

            # MOMENTUM
            if last_ma20 > last_ma50:
                score += 2
                motivi.append("MA20 sopra MA50 (momentum positivo)")

            # VOLUMI
            if last_volume > avg_volume:
                score += 2
                motivi.append("Volumi sopra la media (smart money)")

            # DECISIONE
            if score >= 5:
                azione = "COMPRA"
            elif score >= 3:
                azione = "ATTENDI"
            elif score < 3 and last_price < last_ma50:
                azione = "VENDI"
                motivi.append("Prezzo sotto MA50 (trend negativo)")
            else:
                azione = "NON ENTRARE"

            confidence = round(score / 6, 2)

            risultati[asset] = {
                "score": score,
                "azione": azione,
                "confidence": confidence,
                "motivi": motivi
            }

        except Exception as e:
            risultati[asset] = {
                "score": 0,
                "azione": "ERRORE",
                "confidence": 0,
                "motivi": [str(e)]
            }

    # --- SALVA STORICO ---
    try:
        storico = {}
        if os.path.exists(file_storico):
            with open(file_storico, "r") as f:
                storico = json.load(f)
        storico[datetime.today().strftime("%Y-%m-%d")] = risultati
        with open(file_storico, "w") as f:
            json.dump(storico, f, indent=2)
    except Exception as e:
        print(f"Errore nel salvare lo storico: {e}")

    return risultati
