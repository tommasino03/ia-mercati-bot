import os
from telegram import Bot

def get_env_variables():
    # legge i secrets dall'ambiente, con fallback su valori "hardcoded" per test
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    CHAT_ID = os.environ.get("CHAT_ID")

    if not TELEGRAM_TOKEN or not CHAT_ID:
        # fallback per debug (rimuovere in produzione)
        TELEGRAM_TOKEN = "INSERISCI_IL_TUO_TOKEN_QUI"
        CHAT_ID = "INSERISCI_IL_TUO_CHAT_ID_QUI"

    if not TELEGRAM_TOKEN or not CHAT_ID:
        raise ValueError("TELEGRAM_TOKEN o CHAT_ID mancanti nei Secrets")

    return TELEGRAM_TOKEN, CHAT_ID

def main():
    TELEGRAM_TOKEN, CHAT_ID = get_env_variables()
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text="Bot avviato correttamente!")

if __name__ == "__main__":
    main()
