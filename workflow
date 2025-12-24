name: Aggiorna segnali ogni giorno

on:
  schedule:
    - cron: '0 9 * * *' # ogni giorno alle 09:00 UTC
  workflow_dispatch:

jobs:
  update_signals:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout repository
      uses: actions/checkout@v3

    - name: Aggiorna signals.json realistico con più asset
      run: |
        python3 - <<EOF
        import json, random

        def genera_segnale(nome):
            # Genera score casuale
            score = random.randint(0,6)
            # Logica realistica per azione e importo
            if score >= 4:
                azione = "COMPRA"
                importo = random.choice([100,200])
            elif score >= 2:
                azione = random.choice(["COMPRA","ATTENDI"])
                importo = random.choice([50,100])
            else:
                azione = "ATTENDI"
                importo = 0
            return {"nome": nome, "score": score, "azione": azione, "importo": importo}

        # Lista di tutti gli asset da monitorare
        asset_list = ["NASDAQ", "SP500", "NVIDIA", "TESLA", "ETH-USD", "BTC-USD"]

        # Genera i segnali per tutti gli asset
        data = {
          "aggiornamento": "09:00",
          "segnali": [genera_segnale(nome) for nome in asset_list]
        }

        # Scrive il file signals.json
        with open("signals.json","w") as f:
            json.dump(data,f)
        EOF

    - name: Commit e push
      run: |
        git config --local user.email "github-actions[bot]@users.noreply.github.com"
        git config --local user.name "GitHub Actions"
        git add signals.json
        git commit -m "Aggiornamento automatico segnali realistici con più asset"
        git push
