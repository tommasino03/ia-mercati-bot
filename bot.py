import os
import asyncio
from datetime import datetime
from telegram import Bot
import yfinance as yf
import csv

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

AZIONI_USA = [
    "AAPL", "AMZN", "GOOGL", "META", "TSLA", "NVDA",
    "JPM", "BAC", "V", "MA", "ADBE", "CSCO", "WMT"
]

ETFS = ["SPY", "QQQ", "VTI", "VEA", "EFA"]
EUROPA = ["SAN.MC"]

CSV_FILE = "signals_history.csv"

def analyze(symbol):
    df = yf.download(symbol, period="6mo", interval="1d", progress=False)

    if df.empty or len(df) < 60:
        return None

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
        stato = "FORTE"
    elif score >= 60:
        stato = "POSITIVO"
    elif score >= 40:
        stato = "NEUTRO"
    else:
        stato = "DEBOLE"

    return score, stato

def save_history(date, symbol, score, stato):
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["data", "simbolo", "score", "stato"])
        writer.writerow([date, symbol, score, stato])

def build_report():
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y %H:%M")

    report = f"📊 REPORT IA MERCATI – {date_str}\n\n"
    forti = []

    for symbol in AZIONI_USA + ETFS + EUROPA:
        result = analyze(symbol)
        if not result:
            continue

        score, stato = result
        save_history(date_str, symbol, score, stato)

        report += (
            f"📌 {symbol}\n"
            f"Score: {score}/100\n"
            f"Stato: {stato}\n\n"
        )

        if score >= 80:
            forti.append(symbol)

    report += "🔥 SEGNALI FORTI DEL GIORNO:\n"
    report += ", ".join(forti) if forti else "Nessuno"

    report += (
        "\n\n🧠 STRATEGIA:\n"
        "Entrare solo con score ≥ 80\n"
        "Gestione rischio obbligatoria\n"
    )

    return report

async def main():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=build_report())

if __name__ == "__main__":
    asyncio.run(main())
