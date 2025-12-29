import os
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN mancante nei Secrets GitHub")

# === MESSAGGIO AUTOMATICO ===
async def send_market_study(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    await context.bot.send_message(
        chat_id=chat_id,
        text="📊 Analisi di mercato completata.\n"
             "Trend attuale: rialzista.\n"
             "Volatilità: media.\n"
             "Rischio: controllato."
    )

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot avviato.\n"
        "📈 Analisi di mercato in corso...\n"
        "Riceverai il report tra 2 minuti."
    )

    # invio dopo 120 secondi
    context.job_queue.run_once(
        send_market_study,
        when=120,
        chat_id=update.effective_chat.id,
        name="market_study"
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()

