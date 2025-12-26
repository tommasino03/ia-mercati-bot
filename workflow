name: Python Bot Deployment

on:
  push:
    branches: [ "main" ]
  workflow_dispatch: # Ti permette di avviarlo manualmente

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository content
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10' # Specifica la versione di Python

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          # Installiamo la libreria che manca e altre comuni
          pip install python-telegram-bot

      - name: Run bot
        run: python bot.py
