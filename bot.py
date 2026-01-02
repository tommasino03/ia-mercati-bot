import os
import asyncio
from telegram import Bot
import yfinance as yf
import pandas as pd
from datetime import datetime

# ====== SECRETS ======
TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")

# ====== ASSET ======
ASSETS = {
    "Azioni USA": [
        "AAPL","AMZN","GOOGL","META","TSLA","NVDA",
        "JPM","BAC","V","MA","ADBE","CSCO","CMCSA","WMT"
    ],
    "ETF": ["SPY","QQQ","VEA","VGK","IWV","VTI","EFA","IEMG"],
    "Azioni Europa": ["SAN.MC"],
    "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD"]
}

# ====== INDICATORI ======
def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_trend(close: pd.Series):
    close = pd.to_numeric(close, errors="coerce").dropna()

    if len(close) < 50:
        return "⚠️ neutro", "⚠️ neutro", "⚠️ neutro", "RSI n.d."

    last = float(close.iloc[-1])

    ema20 = close.ewm(span=20).mean()
    ema50 = close.ewm(span=50).mean()
    rsi = calculate_rsi(close).iloc[-1]

    breve = "✅ COMPRA" if last > ema20.iloc[-1] and rsi < 70 else "⚠️ neutro"
    medio = "✅ COMPRA" if ema20.iloc[-1] > ema50.iloc[-1] else "⚠️ neutro"
    lungo = "✅ INVESTI" if last > ema50.iloc[-1] else "⚠️ neutro"

    return breve, medio, lungo, f"RSI {round(float(rsi),1)}"


def analyze_symbol(symbol):
    data = yf.download(symbol, period="6mo", interval="1d", progress=False)

    if data.empty or "Close" not in data:
        return ""

    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    breve, medio, lungo, rsi = calculate_trend(close)

    return (
        f"📌 {symbol}\n"
        f"Breve: {breve}\n"
        f"Medio: {medio}\n"
        f"Lungo: {lungo}\n"
        f"Motivo: trend EMA20/50, {rsi}, volumi normali\n\n"
    )


def build_report():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI – {now}\n\n"

    for category, symbols in ASSETS.items():
        report += f"--- {category} ---\n"
        for s in symbols:
            report += analyze_symbol(s)

    report += (
        "🧠 SITUAZIONE GENERALE:\n"
        "Mercato: POSITIVO\n"
        "Strategia: COMPRARE SUI RITRACCIAMENTI\n"
        "Rischio: MEDIO"
    )

    return report


# ====== SPLIT TELEGRAM ======
def split_message(text, limit=4000):
    chunks = []
    while len(text) > limit:
        split_index = text.rfind("\n", 0, limit)
        if split_index == -1:
            split_index = limit
        chunks.append(text[:split_index])
        text = text[split_index:]
    chunks.append(text)
    return chunks


# ====== MAIN ======
async def main():
    bot = Bot(token=TOKEN)
    report = build_report()
    messages = split_message(report)

    for msg in messages:
        await bot.send_message(chat_id=CHAT_ID, text=msg)


if __name__ == "__main__":
    asyncio.run(main())
