name: Telegram Bot Runner

on:
  push:
    branches: [ "main" ] # Si attiva ogni volta che carichi modifiche
  pull_request:
    branches: [ "main" ]
  schedule:
    - cron: '0 * * * *' # Opzionale: esegue il bot ogni ora (formato POSIX cron)

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout del codice
      uses: actions/checkout@v3

    - name: Configurazione Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10' # Versione stabile di Python

    - name: Installazione dipendenze
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        # Questo comando installa la libreria telegram e le altre nel file requirements

    - name: Esecuzione Bot
      env:
        TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }} # Se usi i "Secrets" di GitHub per il token
      run: python bot.py
