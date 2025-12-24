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

    - name: Aggiorna signals.json in modo realistico
      run: |
        python3 - <<EOF
        import json, random

        def genera_segnale(nome):
            # Genera uno score da 0 a 6
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

        # Lista degli asset
        data = {
          "aggiornamento": "09:00",
          "segnali": [
            genera_segnale("NASDAQ"),
            genera_segnale("SP500"),
            genera_segnale("NVIDIA")
          ]
        }

        # Scrive i dati in signals.json
        with open("signals.json","w") as f:
            json.dump(data,f)
        EOF

    - name: Commit e push
      run: |
        git config --local user.email "github-actions[bot]@users.noreply.github.com"
        git config --local user.name "GitHub Actions"
        git add signals.json
        git commit -m "Aggiornamento automatico segnali realistici"
        git push
