name: Invio segnali bot

on:
  schedule:
    - cron: "0 9 * * *"   # ogni giorno alle 9 UTC
  workflow_dispatch:

jobs:
  run-bot:
    runs-on: ubuntu-latest

    steps:
      - name: Scarica il codice
        uses: actions/checkout@v3

      - name: Imposta Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Installa librerie
        run: |
          python -m pip install --upgrade pip
          pip install yfinance pandas python-telegram-bot==13.15

      - name: Avvia bot
        run: |
          python bot.py
