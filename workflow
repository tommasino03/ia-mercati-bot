name: Invio segnali bot

# Ogni giorno alle 9 UTC + possibilità di esecuzione manuale
on:
  schedule:
    - cron: "0 9 * * *"
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout repository
      uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install yfinance pandas python-telegram-bot --upgrade

    - name: Esegui bot
      run: |
        python bot.py
