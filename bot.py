import yfinance as yf
import asyncio
import os
from telegram import Bot

# =========================
# ENV
# =========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("❌ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti")

bot = Bot(token=TOKEN)

# =========================
# CONFIG
# =========================
TICKERS = ["PLTR", "SOFI", "RIVN", "LCID", "UPST"]

SP500 = "^GSPC"
NASDAQ = "^NDX"
VIX = "^VIX"

MIN_SCORE = 70   # soglia operativa

# =========================
# UTILS
# =========================
def trend_index(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    if df.empty or len(df) < 50:
        return None
    close = df["Close"]
    last = float(close.iloc[-1])
    ma50 = float(close.rolling(50).mean().iloc[-1])
    return "UP" if last > ma50 else "DOWN"

def calcola_rsi(close, periodi=14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(periodi).mean()
    loss = -delta.clip(upper=0).rolling(periodi).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])

# =========================
# STEP 1 – MERCATO
# =========================
def analizza_mercato():
    sp = trend_index(SP500)
    nasdaq = trend_index(NASDAQ)
    vix = yf.download(VIX, period="5d", interval="1d", progress=False)

    if sp is None or nasdaq is None or vix.empty:
        return "NEUTRAL"

    vix_val = float(vix["Close"].iloc[-1])

    if sp == "UP" and nasdaq == "UP" and vix_val < 20:
        return "BULL"
    elif vix_val >= 25:
        return "BEAR"
    else:
        return "NEUTRAL"

# =========================
# STEP 3 – ACCUMULO
# =========================
def rileva_accumulo(df):
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    last = float(close.iloc[-1])

    max_h = float(high.rolling(10).max().iloc[-1])
    min_l = float(low.rolling(10).min().iloc[-1])
    range_pct = (max_h - min_l) / last * 100

    vol_last = float(volume.iloc[-1])
    vol_avg = float(volume.rolling(20).mean().iloc[-1])

    rsi = calcola_rsi(close)

    if range_pct < 4 and vol_last > vol_avg * 1.5 and rsi < 55:
        return "ACCUMULO"
    elif last > max_h * 0.995 and vol_last > vol_avg * 2:
        return "BREAKOUT"
    else:
        return "NONE"

# =========================
# STEP 4 – SIGNAL SCORE
# =========================
def calcola_score(df, mercato, accumulo):
    score = 0

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    last = float(close.iloc[-1])
    rsi = calcola_rsi(close)

    # 1️⃣ Contesto mercato (20)
    if mercato == "BULL":
        score += 20
    elif mercato == "NEUTRAL":
        score += 10

    # 2️⃣ RSI (20)
    if 25 <= rsi <= 40:
        score += 20
    elif 40 < rsi <= 50:
        score += 10

    # 3️⃣ Accumulo / Breakout (25)
    if accumulo == "ACCUMULO":
        score += 18
    elif accumulo == "BREAKOUT":
        score += 25

    # 4️⃣ Trend breve (15)
    ma20 = float(close.rolling(20).mean().iloc[-1])
    if last > ma20:
        score += 15

    # 5️⃣ Risk / Reward (20)
    supporto = float(low.rolling(10).min().iloc[-1])
    resistenza = float(high.rolling(10).max().iloc[-1])

    risk = last - supporto
    reward = resistenza - last

    if reward > risk * 2:
        score += 20
    elif reward > risk:
        score += 10

    return round(score, 1), round(rsi, 1)

# =========================
# SEGNALE
# =========================
def segnale(ticker, mercato):
    df = yf.download(ticker, period="1mo", interval="1d", progress=False)
    if df.empty or len(df) < 30:
        return None

    accumulo = rileva_accumulo(df)
    score, rsi = calcola_score(df, mercato, accumulo)

    if score >= MIN_SCORE:
        azione = "🟢 BUY HIGH QUALITY"
    elif score >= 60:
        azione = "🟡 WATCHLIST"
    else:
        azione = "⛔ NO TRADE"

    return {
        "ticker": ticker,
        "azione": azione,
        "score": score,
        "rsi": rsi,
        "accumulo": accumulo
    }

# =========================
# MAIN
# =========================
async def main():
    mercato = analizza_mercato()
    messaggio = f"📊 MERCATO: {mercato}\n\n"

    for t in TICKERS:
        s = segnale(t, mercato)
        if not s:
            continue

        messaggio += (
            f"{s['ticker']}\n"
            f"{s['azione']}\n"
            f"SCORE: {s['score']}/100\n"
            f"RSI: {s['rsi']}\n"
            f"SETUP: {s['accumulo']}\n\n"
        )

    await bot.send_message(chat_id=CHAT_ID, text=messaggio)

if __name__ == "__main__":
    asyncio.run(main())
