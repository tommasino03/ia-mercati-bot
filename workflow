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
    {"nome": "NASDAQ", "score": 6, "azione": "COMPRA", "importo": 200},
    {"nome": "SP500", "score": 5, "azione": "COMPRA", "importo": 200},
    {"nome": "NVIDIA", "score": 2, "azione": "ATTENDI", "importo": 0}
  ]
}
EOT

      - name: Salva modifiche
        run: |
          git config user.name "github-actions"
          git config user.email "github-actions@users.noreply.github.com"
          git add signals.json
          git commit -m "Aggiornamento automatico signals.json"
          git push
