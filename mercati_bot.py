import os
from telegram import Bot
from telegram.ext import Updater, CommandHandler

TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Devi impostare TELEGRAM_TOKEN come secret su GitHub")

bot = Bot(token=TOKEN)
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Ciao! Bot attivo!")

dispatcher.add_handler(CommandHandler('start', start))

updater.start_polling()
updater.idle()
