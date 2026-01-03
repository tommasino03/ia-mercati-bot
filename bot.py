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
    "JPM","BAC","V","MA","ADBE","CSCO","WMT",
    "SPY","QQQ","VTI","VEA","EFA","SAN.MC"
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
    if last > ma20: score += 30
    if ma20 > ma50: score += 30
    if last > ma50: score += 30
    if last > ma20 and ma20 > ma50: score += 10

    stato = (
        "FORTE" if score >= 80 else
        "POSITIVO" if score >= 60 else
        "NEUTRO" if score >= 40 else
        "DEBOLE"
    )

    return score, stato

def save_history(date, symbol, score, stato):
    exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["data","simbolo","score","stato"])
        w.writerow([date, symbol, score, stato])

def analyze_history():
    if not os.path.isfile(CSV_FILE):
        return "Nessuno storico disponibile."

    stats = {}

    with open(CSV_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            s = row["simbolo"]
            score = int(row["score"])
            stato = row["stato"]

            if s not in stats:
                stats[s] = {"count":0,"forti":0,"tot":0}

            stats[s]["count"] += 1
            stats[s]["tot"] += score
            if stato == "FORTE":
                stats[s]["forti"] += 1

    ranking = sorted(
        stats.items(),
        key=lambda x: (x[1]["forti"], x[1]["tot"]),
        reverse=True
    )

    text = "📈 CLASSIFICA AFFIDABILITÀ (STORICO)\n\n"
    for sym, d in ranking[:5]:
        avg = d["tot"] // d["count"]
        text += (
            f"🔹 {sym}\n"
            f"FORTE: {d['forti']} volte\n"
            f"Score medio: {avg}\n\n"
        )

    return text

def build_report():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI – {now}\n\n"
    forti_today = []

    for symbol in ASSETS:
        res = analyze(symbol)
        if not res:
            continue

        score, stato = res
        save_history(now, symbol, score, stato)

        report += f"📌 {symbol}\nScore: {score}\nStato: {stato}\n\n"
        if stato == "FORTE":
            forti_today.append(symbol)

    report += "🔥 SEGNALI FORTI OGGI:\n"
    report += ", ".join(forti_today) if forti_today else "Nessuno"

    report += "\n\n" + analyze_history()
    return report

async def main():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=build_report())

if __name__ == "__main__":
    asyncio.run(main())
