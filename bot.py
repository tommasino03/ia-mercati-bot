import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === TOKEN ===
TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "❌ BOT_TOKEN non trovato. "
        "Impostalo in GitHub → Settings → Secrets → Actions "
        f"(token ottenuto da {})"
    )

# === HANDLER ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot attivo e funzionante!")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # ⚠️ AVVIO TEMPORANEO (GitHub Actions NON è hosting)
    # Serve solo per testare che il token e il codice siano corretti
    app.run_polling()

if __name__ == "__main__":
    main()
