import os
import asyncio
from datetime import datetime
from telegram import Bot
import yfinance as yf

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

AZIONI_USA = [
    "AAPL", "AMZN", "GOOGL", "META", "TSLA", "NVDA",
    "JPM", "BAC", "V", "MA", "ADBE", "CSCO", "CMCSA", "WMT"
]

ETFS = ["SPY", "QQQ", "VEA", "VGK", "IWV", "VTI", "EFA", "IEMG"]
EUROPA = ["SAN.MC"]

def analyze(symbol):
    df = yf.download(symbol, period="6mo", interval="1d", progress=False)

    if df.empty or len(df) < 60:
        return f"📌 {symbol}\nDati insufficienti\n\n", 0

    close = df["Close"].tolist()
    last = close[-1]
    ma20 = sum(close[-20:]) / 20
    ma50 = sum(close[-50:]) / 50

    score = 0
    if last > ma20:
        score += 30
    if ma20 > ma50:
        score += 30
    if last > ma50:
        score += 30
    if last > ma20 and ma20 > ma50:
        score += 10

    if score >= 80:
        rating = "🔥 SEGNALE FORTE"
    elif score >= 60:
        rating = "✅ POSITIVO"
    elif score >= 40:
        rating = "⚠️ NEUTRO"
    else:
        rating = "❌ DEBOLE"

    return f"""📌 {symbol}
Score: {score}/100
Valutazione: {rating}

""", score

def build_report():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI – {now}\n\n"

    forti = []

    for titolo in AZIONI_USA + ETFS + EUROPA:
        testo, score = analyze(titolo)
        report += testo
        if score >= 80:
            forti.append(titolo)

    report += "\n🔥 SEGNALI FORTI DEL GIORNO:\n"
    report += ", ".join(forti) if forti else "Nessuno"

    report += (
        "\n\n🧠 STRATEGIA:\n"
        "Entrare solo sui titoli con score ≥ 80\n"
        "Rischio: MEDIO\n"
    )

    return report

async def main():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=build_report())

if __name__ == "__main__":
    asyncio.run(main())
