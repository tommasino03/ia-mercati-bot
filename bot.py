import os
import asyncio
from datetime import datetime
from telegram import Bot
import yfinance as yf
import csv

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ASSETS = [
    "AAPL","AMZN","GOOGL","META","TSLA","NVDA",
    "JPM","BAC","V","MA","SPY","QQQ","VTI"
]

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
    if last > ma20: score += 25
    if ma20 > ma50: score += 25
    if last > ma50: score += 20
    if abs(ma20 - ma50) / ma50 < 0.05: score += 15

    storico = storico_forte(symbol)
    if storico >= 3: score += 15

    decisione = (
        "🟢 COMPRA" if score >= 80 else
        "🟡 ASPETTA" if score >= 60 else
        "🔴 EVITA"
    )

    return score, decisione

def storico_forte(symbol):
    if not os.path.isfile(CSV_FILE):
        return 0

    count = 0
    with open(CSV_FILE) as f:
        r = csv.DictReader(f)
        for row in r:
            if row["simbolo"] == symbol and int(row["score"]) >= 80:
                count += 1
    return count

def save_history(date, symbol, score, decisione):
    exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["data","simbolo","score","decisione"])
        w.writerow([date, symbol, score, decisione])

def build_report():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"💎 IA MERCATI – VERSIONE PREMIUM\n🕒 {now}\n\n"

    for symbol in ASSETS:
        res = analyze(symbol)
        if not res:
            continue

        score, decisione = res
        save_history(now, symbol, score, decisione)

        report += (
            f"📌 {symbol}\n"
            f"Score: {score}/100\n"
            f"Decisione: {decisione}\n\n"
        )

    report += "⚠️ NON è un consiglio finanziario"
    return report

async def main():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=build_report())

if __name__ == "__main__":
    asyncio.run(main())
