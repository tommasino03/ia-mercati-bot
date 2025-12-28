import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")  # Inserisci il token del tuo bot come variabile d'ambiente

# Esempio semplice di comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Il bot è attivo e funzionante 🚀")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Aggiungi i comandi
    app.add_handler(CommandHandler("start", start))

    # Avvio del webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        url_path=TOKEN,
        webhook_url=f"https://{os.environ.get('PROJECT_DOMAIN')}.repl.co/{TOKEN}"  # Cambia se non usi Replit
    )

if __name__ == "__main__":
    main()
