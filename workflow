name: IA Mercati Bot

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  run-bot:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Show repo files (debug)
        run: ls -la

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Show python and pip (debug)
        run: |
          python --version
          python -m pip --version

      - name: Show requirements.txt (debug)
        run: |
          if [ -f requirements.txt ]; then echo "requirements.txt content:"; cat requirements.txt; else echo "NO requirements.txt"; fi

      - name: Uninstall wrong 'telegram' package if present (debug)
        run: python -m pip uninstall -y telegram || true

      - name: Install dependencies from requirements.txt
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r requirements.txt

      - name: Show installed packages (debug)
        run: python -m pip show python-telegram-bot || python -m pip list

      - name: Run bot
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
        run: python bot.py
