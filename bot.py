import os
import asyncio
from datetime import datetime
import yfinance as yf
import pandas as pd
import requests
from telegram import Bot

TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise RuntimeError("BOT_TOKEN o CHAT_ID mancanti")

AZIONI_USA = ["AAPL","AMZN","GOOGL","META","TSLA","NVDA","JPM","BAC","V","MA"]
ETF = ["SPY","QQQ","VTI"]
AZIONI_EUROPA = ["SAN.MC"]
CRYPTO = ["bitcoin","ethereum"]

# ================= TREND IA SMART =================
def calculate_trend(prices: pd.Series, volumes: pd.Series | None = None):
    if prices.empty or len(prices) < 60:
        return "⚠️ HOLD", "Dati insufficienti"

    prices = prices.astype(float)

    sma5 = prices.rolling(5).mean().iloc[-1]
    sma20 = prices.rolling(20).mean().iloc[-1]
    sma50 = prices.rolling(50).mean().iloc[-1]
    last = prices.iloc[-1]

    volume_ok = True
    if volumes is not None and not volumes.empty:
        vol_mean = volumes.rolling(20).mean().iloc[-1]
        vol_last = volumes.iloc[-1]
        volume_ok = vol_last >= vol_mean

    if last > sma5 > sma20 > sma50 and volume_ok:
        return "🟢 BUY", "Trend rialzista forte + volumi"
    elif last < sma20:
        return "🔴 SELL", "Prezzo sotto SMA20"
    else:
        return "🟡 HOLD", "Trend laterale / in attesa"

# ================= REPORT =================
def build_report():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI SMART – {now}\n\n"

    report += "--- AZIONI USA ---\n"
    for t in AZIONI_USA:
        try:
            df = yf.download(t, period="3mo", interval="1d", progress=False)
            signal, reason = calculate_trend(df["Close"], df["Volume"])
        except Exception:
            signal, reason = "⚠️ HOLD", "Errore dati"
        report += f"📌 {t}\nSegnale: {signal}\nMotivo: {reason}\n\n"

    report += "--- ETF ---\n"
    for t in ETF:
        try:
            df = yf.download(t, period="3mo", interval="1d", progress=False)
            signal, reason = calculate_trend(df["Close"], df["Volume"])
        except Exception:
            signal, reason = "⚠️ HOLD", "Errore dati"
        report += f"📌 {t}\nSegnale: {signal}\nMotivo: {reason}\n\n"

    report += "--- CRYPTO ---\n"
    for coin in CRYPTO:
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart?vs_currency=usd&days=90"
            data = requests.get(url, timeout=10).json()
            prices = pd.Series([p[1] for p in data["prices"]])
            signal, reason = calculate_trend(prices)
        except Exception:
            signal, reason = "⚠️ HOLD", "Errore dati"
        report += f"📌 {coin.upper()}\nSegnale: {signal}\nMotivo: {reason}\n\n"

    report += (
        "🧠 STRATEGIA IA:\n"
        "✔ BUY solo su trend confermati\n"
        "✔ HOLD su mercati incerti\n"
        "✔ SELL su rottura supporti\n"
        "⚠️ Rischio: MEDIO\n"
    )

    return report

# ================= TELEGRAM =================
async def main():
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=build_report())

if __name__ == "__main__":
    asyncio.run(main())
