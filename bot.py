import os
import asyncio
from datetime import datetime
import yfinance as yf
import pandas as pd
import requests
from telegram import Bot

# ================= CONFIG =================
TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise RuntimeError("BOT_TOKEN o CHAT_ID mancanti nei Secrets GitHub")

AZIONI_USA = ["AAPL", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "JPM", "BAC", "V", "MA"]
ETF = ["SPY", "QQQ", "VTI"]
AZIONI_EUROPA = ["SAN.MC"]
CRYPTO = ["bitcoin", "ethereum"]

# ================= ANALISI IA =================
def calculate_trend(prices: pd.Series, volumes: pd.Series | None = None):
    try:
        if prices.empty or len(prices) < 60:
            return "⚠️ HOLD", "Dati insufficienti"

        prices = prices.astype(float)

        # Medie mobili
        sma20 = prices.rolling(20).mean()
        sma50 = prices.rolling(50).mean()

        last_price = prices.iloc[-1]

        # RSI
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_last = rsi.iloc[-1]

        # MACD
        ema12 = prices.ewm(span=12, adjust=False).mean()
        ema26 = prices.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()

        macd_last = macd.iloc[-1]
        signal_last = signal.iloc[-1]

        # Volume
        volume_ok = True
        if volumes is not None and not volumes.empty:
            volumes = volumes.astype(float)
            volume_ok = volumes.iloc[-1] >= volumes.rolling(20).mean().iloc[-1]

        # LOGICA FINALE
        if (
            last_price > sma20.iloc[-1] > sma50.iloc[-1]
            and macd_last > signal_last
            and rsi_last < 70
            and volume_ok
        ):
            return "🟢 BUY", f"Trend forte | RSI {round(rsi_last,1)} | MACD positivo"

        if rsi_last > 70:
            return "🔴 SELL", f"Ipercomprato | RSI {round(rsi_last,1)}"

        if last_price < sma20.iloc[-1]:
            return "🔴 SELL", "Rottura supporto SMA20"

        return "🟡 HOLD", f"Laterale | RSI {round(rsi_last,1)}"

    except Exception:
        return "⚠️ HOLD", "Errore calcolo"

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
            prices = pd.Series([p[1] for p in data.get("prices", [])])
            signal, reason = calculate_trend(prices)
        except Exception:
            signal, reason = "⚠️ HOLD", "Errore dati"
        report += f"📌 {coin.upper()}\nSegnale: {signal}\nMotivo: {reason}\n\n"

    report += (
        "🧠 STRATEGIA IA:\n"
        "✔ BUY solo su trend confermati\n"
        "✔ HOLD su mercati incerti\n"
        "✔ SELL su rotture o ipercomprato\n"
        "⚠️ Rischio: MEDIO"
    )

    return report

# ================= TELEGRAM =================
async def main():
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=build_report())

if __name__ == "__main__":
    asyncio.run(main())
