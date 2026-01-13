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

MIN_SCORE = 70

CAPITALE = 10_000
RISCHIO_PERC = 0.01

ATR_MULT = 1.5

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

def calcola_atr(df, periodi=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    tr = (
        (high - low)
        .to_frame("hl")
        .join((high - close.shift()).abs().to_frame("hc"))
        .join((low - close.shift()).abs().to_frame("lc"))
        .max(axis=1)
    )

    atr = tr.rolling(periodi).mean()
    return float(atr.iloc[-1])

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
# STEP 4 – SCORE
# =========================
def calcola_score(df, mercato, accumulo):
    score = 0
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    last = float(close.iloc[-1])
    rsi = calcola_rsi(close)

    if mercato == "BULL":
        score += 20
    elif mercato == "NEUTRAL":
        score += 10

    if 25 <= rsi <= 40:
        score += 20
    elif 40 < rsi <= 50:
        score += 10

    if accumulo == "ACCUMULO":
        score += 18
    elif accumulo == "BREAKOUT":
        score += 25

    ma20 = float(close.rolling(20).mean().iloc[-1])
    if last > ma20:
        score += 15

    supporto = float(low.rolling(10).min().iloc[-1])
    resistenza = float(high.rolling(10).max().iloc[-1])

    risk = last - supporto
    reward = resistenza - last

    if reward > risk * 2:
        score += 20
    elif reward > risk:
        score += 10

    return round(score, 1), round(rsi, 1), supporto

# =========================
# STEP 5 – POSITION SIZE
# =========================
def calcola_position_size(prezzo, stop):
    rischio_trade = CAPITALE * RISCHIO_PERC
    rischio_unit = prezzo - stop

    if rischio_unit <= 0:
        return 0

    qty = int(rischio_trade / rischio_unit)
    return qty if qty > 0 else 0

# =========================
# STEP 6 – TRAILING STOP
# =========================
def trailing_stop(entry, stop, df):
    close = df["Close"]
    high = df["High"]

    last = float(close.iloc[-1])
    atr = calcola_atr(df)

    # Break-even
    if last >= entry + (entry - stop):
        stop = max(stop, entry)

    # Trailing ATR
    new_stop = float(high.iloc[-1]) - atr * ATR_MULT
    stop = max(stop, new_stop)

    return round(stop, 2)

# =========================
# SEGNALE
# =========================
def segnale(ticker, mercato):
    df = yf.download(ticker, period="2mo", interval="1d", progress=False)
    if df.empty or len(df) < 30:
        return None

    accumulo = rileva_accumulo(df)
    score, rsi, stop = calcola_score(df, mercato, accumulo)
    last = float(df["Close"].iloc[-1])

    if score < MIN_SCORE:
        return None

    qty = calcola_position_size(last, stop)
    if qty == 0:
        return None

    stop_trail = trailing_stop(last, stop, df)

    return {
        "ticker": ticker,
        "prezzo": round(last, 2),
        "stop": round(stop, 2),
        "stop_trailing": stop_trail,
        "qty": qty,
        "score": score,
        "rsi": rsi
    }

# =========================
# MAIN
# =========================
async def main():
    mercato = analizza_mercato()
    msg = f"📊 MERCATO: {mercato}\n\n"

    for t in TICKERS:
        s = segnale(t, mercato)
        if not s:
            continue

        msg += (
            f"🟢 {s['ticker']} BUY\n"
            f"Prezzo: {s['prezzo']}\n"
            f"Stop iniziale: {s['stop']}\n"
            f"Stop trailing: {s['stop_trailing']}\n"
            f"Quantità: {s['qty']}\n"
            f"SCORE: {s['score']}\n"
            f"RSI: {s['rsi']}\n\n"
        )

    if msg.strip():
        await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
