name: Invio segnali bot

on:
  schedule:
    - cron: "0 9 * * *"
  workflow_dispatch:

jobs:
  run-bot:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Installa librerie
        run: |
          pip install yfinance pandas requests

      - name: Avvia bot
        run: |
          python bot.py
