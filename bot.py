import os
import asyncio
from telegram import Bot

TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN mancante nei GitHub Secrets")

if not CHAT_ID:
    raise RuntimeError("❌ CHAT_ID mancante nei GitHub Secrets")

async def main():
    bot = Bot(token=TOKEN)

    message = (
        "📊 *Studio del mercato – Report giornaliero*\n\n"
        "📈 Trend principale: rialzista\n"
        "📉 Volatilità: moderata\n"
        "⚠️ Rischio: medio\n\n"
        "🧠 Strategia suggerita:\n"
        "- Attendere conferme\n"
        "- Gestione rischio attiva\n"
        "- No overtrading\n\n"
        "⏰ Report generato automaticamente"
    )

    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    asyncio.run(main())
