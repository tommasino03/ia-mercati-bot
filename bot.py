import yfinance as yf
import asyncio
import os
from telegram import Bot
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

# =====================
# ENV
# =====================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("❌ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti")

bot = Bot(token=TOKEN)

# =====================
# CONFIG
# =====================
TICKERS = ["PLTR", "SOFI", "RIVN", "LCID", "UPST"]
TICKERS_ANOMALI = ["AMC", "GME", "BB", "KOSS", "NOK"]
RSI_BUY = 30
RSI_SELL = 70

# =====================
# RSI
# =====================
def calcola_rsi(close, periodi=14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(periodi).mean()
    loss = -delta.clip(upper=0).rolling(periodi).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])

# =====================
# SCORE
# =====================
def calcola_score(rsi, vol_att, vol_avg, move):
    score = 0
    # RSI
    if rsi <= 25:
        score += 40
    elif rsi <= 30:
        score += 30
    elif rsi <= 35:
        score += 20
    # Volume
    ratio = vol_att / vol_avg if vol_avg > 0 else 0
    if ratio >= 3:
        score += 40
    elif ratio >= 2:
        score += 30
    elif ratio >= 1.5:
        score += 20
    # Movimento
    if abs(move) >= 5:
        score += 20
    elif abs(move) >= 3:
        score += 15
    elif abs(move) >= 2:
        score += 10
    return score

# =====================
# ANALISI TICKER
# =====================
def analizza_ticker(ticker):
    df = yf.download(ticker, period="1d", interval="5m", progress=False)
    if df.empty or len(df) < 30:
        return None

    open_p = float(df["Open"].iloc[0])
    last_p = float(df["Close"].iloc[-1])
    move = round(((last_p - open_p) / open_p) * 100, 2)

    rsi = calcola_rsi(df["Close"])

    vol_att = float(df["Volume"].iloc[-1])
    vol_avg = float(df["Volume"].rolling(20).mean().iloc[-1])

    # Media mobile
    ma20 = float(df["Close"].rolling(20).mean().iloc[-1])
    ma50 = float(df["Close"].rolling(50).mean().iloc[-1]) if len(df) >= 50 else ma20
    ma200 = float(df["Close"].rolling(200).mean().iloc[-1]) if len(df) >= 200 else ma20

    above_ma = "sopra" if last_p > ma20 else "sotto"

    score = calcola_score(rsi, vol_att, vol_avg, move)

    if score >= 80:
        segnale = "🚀 SEGNALE FORTISSIMO"
    elif score >= 60:
        segnale = "✅ BUON SEGNALE"
    elif score >= 40:
        segnale = "⚠️ SEGNALE DEBOLE"
    else:
        segnale = "⏸ IGNORA"

    return {
        "ticker": ticker,
        "df": df,
        "move": move,
        "rsi": rsi,
        "score": score,
        "segnale": segnale,
        "above_ma": above_ma,
        "ma20": ma20,
        "ma50": ma50,
        "ma200": ma200
    }

# =====================
# GRAFICO
# =====================
def salva_grafico(df, ticker):
    plt.figure(figsize=(8,4))
    plt.plot(df.index, df["Close"], label="Close")
    plt.plot(df.index, df["Close"].rolling(20).mean(), label="MA20")
    plt.plot(df.index, df["Close"].rolling(50).mean(), label="MA50")
    plt.plot(df.index, df["Close"].rolling(200).mean(), label="MA200")
    plt.title(f"{ticker} intraday")
    plt.xlabel("Time")
    plt.ylabel("Prezzo")
    plt.legend()
    plt.grid(True)
    filename = f"{ticker}.png"
    plt.savefig(filename)
    plt.close()
    return filename

# =====================
# MAIN TOP3 + ANOMALI + GRAFICI
# =====================
async def main():
    risultati = []

    for t in TICKERS + TICKERS_ANOMALI:
        d = analizza_ticker(t)
        if d:
            risultati.append(d)

    if not risultati:
        await bot.send_message(chat_id=CHAT_ID, text="❌ Nessun dato valido oggi")
        return

    # TOP3 score
    top3 = sorted(risultati, key=lambda x: x["score"], reverse=True)[:3]

    messaggio = "📊 TOP 3 SEGNALE MERCATO\n\n"
    for d in top3:
        messaggio += (
            f"{d['ticker']}\n"
            f"Move: {d['move']}%\n"
            f"RSI: {d['rsi']}\n"
            f"SCORE: {d['score']}/100\n"
            f"Segnale: {d['segnale']}\n"
            f"Prezzo {d['above_ma']} MA20\n\n"
        )

        grafico = salva_grafico(d["df"], d["ticker"])
        await bot.send_photo(chat_id=CHAT_ID, photo=open(grafico, "rb"))

if __name__ == "__main__":
    asyncio.run(main())
