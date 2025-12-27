nome : IA Mercati Bot

SU :
  programma :
    - cron : " 0 7 * * * "
  workflow_dispatch :

lavori :
  esegui-bot :
    in esecuzione : ubuntu-latest
    passaggi :
      - usi : azioni/checkout@v3

      - nome : installa le dipendenze
        esegui : pip install yfinance requests

      - nome : Esegui bot
        esegui : python bot.py
