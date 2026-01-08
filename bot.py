import os
import asyncio
import yfinance as yf
from telegram import Bot


def get_env():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token or not chat_id:
        raise ValueError("TELEGRAM_TOKEN o CHAT_ID mancanti")

    return token, chat_id


def get_price(ticker: str):
    try:
        data = yf.download(ticker, period="5d", interval="1d", progress=False)

        if data.empty or "Close" not in data:
            return None

        last = float(data["Close"].iloc[-1])
        prev = float(data["Close"].iloc[-2])
        change = ((last - prev) / prev) * 100

        return round(last, 2), round(change, 2)

    except Exception:
        return None


async def main():
    token, chat_id = get_env()
    bot = Bot(token=token)

    assets = {
        "📱 Apple (AAPL)": "AAPL",
        "📊 S&P 500": "^GSPC",
        "💻 Nasdaq": "^IXIC"
    }

    message = "📈 *Mini Report Mercati*\n\n"

    for name, ticker in assets.items():
        result = get_price(ticker)

        if result:
            price, change = result
            emoji = "🟢" if change >= 0 else "🔴"
            message += f"{name}\nPrezzo: {price}\nVariazione: {emoji} {change}%\n\n"
        else:
            message += f"{name}\n⚠️ Dati non disponibili\n\n"

    await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="Markdown"
    )


if __name__ == "__main__":
    asyncio.run(main())
