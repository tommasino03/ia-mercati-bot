import os
from telegram import Bot
from telegram.ext import Updater, CommandHandler

# Prende il token dal secret di GitHub
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Devi impostare TELEGRAM_TOKEN come secret su GitHub")

# Setup bot
bot = Bot(token=TOKEN)
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Comando /start
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Ciao! Bot attivo!")

dispatcher.add_handler(CommandHandler('start', start))

# Avvia il bot
updater.start_polling()
updater.idle()
