import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === TOKEN ===
TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "❌ BOT_TOKEN non trovato. "
        "Impostalo in GitHub → Settings → Secrets → Actions "
        "e incolla il token ottenuto da @BotFather"
    )

# === HANDLER ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot attivo e funzionante!")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # ⚠️ GitHub Actions NON è un hosting permanente
    # Polling usato SOLO per test
    app.run_polling()

if __name__ == "__main__":
    main()
