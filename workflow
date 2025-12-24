name: Aggiorna signals.json

on:
  schedule:
    - cron: '0 9 * * *'  # ogni giorno alle 9:00 UTC
  workflow_dispatch:  # permette anche di far partire manualmente

jobs:
  aggiorna:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Aggiorna signals.json
        run: |
          echo "Creiamo segnali di esempio"
          TODAY=$(date +'%Y-%m-%d')
          cat <<EOT > signals.json
{
  "aggiornamento": "$TODAY",
  "segnali": [
   assets = [
    assets = [
    {"nome": "NASDAQ", "ticker": "^IXIC"},
    {"nome": "SP500", "ticker": "^GSPC"},
    {"nome": "NVIDIA", "ticker": "NVDA"},
    {"nome": "TESLA", "ticker": "TSLA"},
    {"nome": "APPLE", "ticker": "AAPL"},
    {"nome": "MICROSOFT", "ticker": "MSFT"},
    {"nome": "BTC", "ticker": "BTC-USD"},
    {"nome": "ETH", "ticker": "ETH-USD"},
    {"nome": "CARDANO", "ticker": "ADA-USD"},
    {"nome": "SOLANA", "ticker": "SOL-USD"}
]


}
EOT

      - name: Salva modifiche
           - name: Aggiorna signals.json dinamicamente
      run: |
        python3 - <<EOF
        import json, random
        data = {
          "aggiornamento": "09:00",
          "segnali": [
            {"nome": "NASDAQ", "score": random.randint(0,6), "azione": random.choice(["COMPRA","ATTENDI"]), "importo": random.choice([0,50,100,200])},
            {"nome": "SP500", "score": random.randint(0,6), "azione": random.choice(["COMPRA","ATTENDI"]), "importo": random.choice([0,50,100,200])},
            {"nome": "NVIDIA", "score": random.randint(0,6), "azione": random.choice(["COMPRA","ATTENDI"]), "importo": random.choice([0,50,100,200])}
          ]
        }
        with open("signals.json","w") as f:
            json.dump(data,f)
        EOF
