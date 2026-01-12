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
# INDICI MERCATO
# =========================
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

    if last > ma50:
        return "UP"
    else:
        return "DOWN"

def valore_attuale(ticker):
    df = yf.download(ticker, period="5d", interval="1d", progress=False)

    if df.empty:
        return None

    return float(df["Close"].iloc[-1])

# =========================
# ANALISI CONTESTO MERCATO
# =========================
def analizza_mercato():
    sp_trend = trend_index(SP500)
    nasdaq_trend = trend_index(NASDAQ)
    vix_value = valore_attuale(VIX)

    if sp_trend is None or nasdaq_trend is None or vix_value is None:
        return {
            "status": "⚠️ DATI NON DISPONIBILI",
            "tradabile": False,
            "sp500": "N/A",
            "nasdaq": "N/A",
            "vix": "N/A"
        }

    if sp_trend == "UP" and nasdaq_trend == "UP" and vix_value < 20:
        stato = "🟢 MERCATO FAVOREVOLE (RISK ON)"
        tradabile = True
    elif vix_value >= 25 or (sp_trend == "DOWN" and nasdaq_trend == "DOWN"):
        stato = "🔴 MERCATO RISK-OFF (STOP BUY)"
        tradabile = False
    else:
        stato = "🟡 MERCATO NEUTRO (ATTENZIONE)"
        tradabile = False

    return {
        "status": stato,
        "tradabile": tradabile,
        "sp500": sp_trend,
        "nasdaq": nasdaq_trend,
        "vix": round(vix_value, 2)
    }

# =========================
# MAIN
# =========================
async def main():
    mercato = analizza_mercato()

    messaggio = (
        "📊 CONTESTO DI MERCATO\n\n"
        f"S&P 500: {mercato['sp500']}\n"
        f"Nasdaq: {mercato['nasdaq']}\n"
        f"VIX: {mercato['vix']}\n\n"
        f"➡️ {mercato['status']}"
    )

    await bot.send_message(chat_id=CHAT_ID, text=messaggio)

if __name__ == "__main__":
    asyncio.run(main())
