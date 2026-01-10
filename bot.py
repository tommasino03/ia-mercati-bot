import os
import asyncio
from datetime import datetime
from telegram import Bot
import yfinance as yf
import matplotlib.pyplot as plt

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print("TOKEN:", "OK" if TOKEN else "MANCANTE")
print("CHAT_ID:", "OK" if CHAT_ID else "MANCANTE")

# CONFIG
SOGLIA_INTRADAY = 2.0
NUM_TOP_VOL = 10

PRINCIPALI = {
    "₿ Bitcoin": "BTC-USD",
    "📈 S&P 500": "^GSPC",
    "💻 Nasdaq": "^IXIC"
}

SMALL_CAPS = [
    "PLTR","NIO","RIVN","COIN","LCID","SOFI","AFRM","SNAP","TWLO","FUBO",
    "MARA","HUT","RIOT","ETSY","DDOG","UBER","LYFT","CRWD","DOCU","SQ",
    "GME","AMC","SNDL","BB","SPCE","FCEL"
]

def intraday_move(ticker):
    try:
        df = yf.download(
            ticker,
            period="1d",
            interval="1h",
            progress=False
        )

        if df is None or df.empty or len(df) < 2:
            return None

        open_price = df["Open"].iloc[0]
        last_price = df["Close"].iloc[-1]

        if open_price == 0:
            return None

        return round((last_price / open_price - 1) * 100, 2)

    except Exception as e:
        print(f"Errore intraday {ticker}: {e}")
        return None

def grafico_smallcap(alerts):
    tickers = list(alerts.keys())
    valori = list(alerts.values())

    plt.figure(figsize=(10,6))
    plt.bar(
        tickers,
        valori,
        color=["green" if v > 0 else "red" for v in valori]
    )
    plt.axhline(0, color="black")
    plt.title("Small-cap – Movimento Intraday %")
    plt.ylabel("%")
    plt.tight_layout()

    path = "/tmp/intraday_smallcap.png"
    plt.savefig(path)
    plt.close()
    return path

async def main():
    if not TOKEN or not CHAT_ID:
        raise ValueError("❌ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti")

    bot = Bot(token=TOKEN)
    msg = f"⏱️ ALERT INTRADAY – {datetime.now().strftime('%H:%M')}\n\n"
    alert = False

    # 🔹 PRINCIPALI
    for nome, ticker in PRINCIPALI.items():
        move = intraday_move(ticker)
        if move is not None and abs(move) >= SOGLIA_INTRADAY:
            alert = True
            simbolo = "⬆️" if move > 0 else "⬇️"
            msg += f"{nome}: {simbolo} {move}%\n"

    # 🔹 SMALL-CAP
    small_alerts = {}
    for ticker in SMALL_CAPS:
        move = intraday_move(ticker)
        if move is not None and abs(move) >= SOGLIA_INTRADAY:
            small_alerts[ticker] = move

    if small_alerts:
        alert = True
        top = dict(
            sorted(
                small_alerts.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:NUM_TOP_VOL]
        )

        msg += "\n📊 Small-cap intraday:\n"
        for t, v in top.items():
            simbolo = "⬆️" if v > 0 else "⬇️"
            msg += f"{t}: {simbolo} {v}%\n"

        grafico = grafico_smallcap(top)
    else:
        grafico = None

    if alert:
        if grafico:
            await bot.send_photo(
                chat_id=int(CHAT_ID),
                photo=open(grafico, "rb"),
                caption=msg
            )
        else:
            await bot.send_message(
                chat_id=int(CHAT_ID),
                text=msg
            )
    else:
        print("Nessun movimento intraday rilevante")

if __name__ == "__main__":
    asyncio.run(main())
