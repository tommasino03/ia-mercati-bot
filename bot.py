import yfinance as yf
import asyncio
import os
from telegram import Bot

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
TICKERS_ANOMALI = ["AMC", "GME", "BB", "KOSS", "NOK"]  # piccole/volatili
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
        "move": move,
        "rsi": rsi,
        "score": score,
        "segnale": segnale
    }

# =====================
# MAIN RANKING TOP3 + ANOMALI
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

    # Ordina per score decrescente e prendi top 3
    top3 = sorted(risultati, key=lambda x: x["score"], reverse=True)[:3]

    messaggio = "📊 TOP 3 + TITOLO ANOMALO\n\n"
    for d in top3:
        messaggio += (
            f"{d['ticker']}\n"
            f"Move: {d['move']}%\n"
            f"RSI: {d['rsi']}\n"
            f"SCORE: {d['score']}/100\n"
            f"Segnale: {d['segnale']}\n\n"
        )

    await bot.send_message(chat_id=CHAT_ID, text=messaggio)

if __name__ == "__main__":
    asyncio.run(main())
