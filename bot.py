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

# =========================
# UTILS SICURI
# =========================
def trend_index(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    if df.empty or len(df) < 50:
        return None
    close = df["Close"]
    last = float(close.iloc[-1])
    ma50 = float(close.rolling(50).mean().iloc[-1])
    return "UP" if last > ma50 else "DOWN"

def valore_attuale(ticker):
    df = yf.download(ticker, period="5d", interval="1d", progress=False)
    if df.empty:
        return None
    return float(df["Close"].iloc[-1])

def calcola_rsi(close, periodi=14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(periodi).mean()
    loss = -delta.clip(upper=0).rolling(periodi).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])

# =========================
# STEP 1 – CONTESTO
# =========================
def analizza_mercato():
    sp = trend_index(SP500)
    nasdaq = trend_index(NASDAQ)
    vix = valore_attuale(VIX)

    if sp is None or nasdaq is None or vix is None:
        return "NEUTRAL"

    if sp == "UP" and nasdaq == "UP" and vix < 20:
        return "BULL"
    elif vix >= 25:
        return "BEAR"
    else:
        return "NEUTRAL"

# =========================
# STEP 3 – ACCUMULO ISTITUZIONALE
# =========================
def rileva_accumulo(df):
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    last = float(close.iloc[-1])

    # Range stretto (ultimi 10 giorni)
    max_h = float(high.rolling(10).max().iloc[-1])
    min_l = float(low.rolling(10).min().iloc[-1])
    range_pct = (max_h - min_l) / last * 100

    # Volume
    vol_last = float(volume.iloc[-1])
    vol_avg = float(volume.rolling(20).mean().iloc[-1])

    rsi = calcola_rsi(close)

    if range_pct < 4 and vol_last > vol_avg * 1.5 and rsi < 55:
        return "🧠 ACCUMULO"
    elif last > max_h * 0.995 and vol_last > vol_avg * 2:
        return "🚀 BREAKOUT"
    else:
        return "⏳ IN ATTESA"

# =========================
# STEP 2 – SEGNALE OPERATIVO
# =========================
def segnale_operativo(ticker, mercato):
    df = yf.download(ticker, period="1mo", interval="1d", progress=False)
    if df.empty or len(df) < 30:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    last = float(close.iloc[-1])
    rsi = calcola_rsi(close)

    supporto = float(low.rolling(10).min().iloc[-1])
    resistenza = float(high.rolling(10).max().iloc[-1])

    entry = last
    stop = round(supporto * 0.99, 2)
    target = round(resistenza * 1.01, 2)

    accumulo = rileva_accumulo(df)

    if mercato == "BULL" and rsi < 35 and accumulo in ["🧠 ACCUMULO", "🚀 BREAKOUT"]:
        azione = "🟢 BUY (setup istituzionale)"
    elif accumulo == "🚀 BREAKOUT" and mercato != "BEAR":
        azione = "🚀 BUY BREAKOUT"
    elif rsi > 70:
        azione = "🔴 SELL / TAKE PROFIT"
    elif mercato == "BEAR":
        azione = "⛔ NO TRADE (mercato negativo)"
    else:
        azione = "🟡 WAIT"

    return {
        "ticker": ticker,
        "azione": azione,
        "accumulo": accumulo,
        "entry": round(entry, 2),
        "stop": stop,
        "target": target,
        "rsi": round(rsi, 1)
    }

# =========================
# MAIN
# =========================
async def main():
    mercato = analizza_mercato()

    header = {
        "BULL": "🟢 MERCATO FAVOREVOLE",
        "BEAR": "🔴 MERCATO RISK-OFF",
        "NEUTRAL": "🟡 MERCATO NEUTRO"
    }

    messaggio = f"📊 CONTESTO MERCATO\n{header[mercato]}\n\n"

    for t in TICKERS:
        s = segnale_operativo(t, mercato)
        if not s:
            continue

        messaggio += (
            f"{s['ticker']}\n"
            f"{s['azione']}\n"
            f"{s['accumulo']}\n"
            f"RSI: {s['rsi']}\n"
            f"Entry: {s['entry']}\n"
            f"Stop: {s['stop']}\n"
            f"Target: {s['target']}\n\n"
        )

    await bot.send_message(chat_id=CHAT_ID, text=messaggio)

if __name__ == "__main__":
    asyncio.run(main())
