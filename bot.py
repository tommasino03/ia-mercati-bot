import os
import asyncio
from datetime import datetime, timedelta
from telegram import Bot
import yfinance as yf
import feedparser

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print("TOKEN:", "OK" if TOKEN else "MANCANTE")
print("CHAT_ID:", "OK" if CHAT_ID else "MANCANTE")

# Configurazioni
SOGLIA_VOLATILITA = 2.0   # % minimo di variazione anomala
GIORNI_MEDIA = 5           # giorni per calcolare media storica
TICKER_MINORI = ["TSLA", "PLTR", "NIO", "RIVN", "COIN"]  # esempi, puoi aggiungere altri

RSS_FEED = "https://www.coindesk.com/arc/outboundfeeds/rss/"  # esempio news crypto

# Funzione per calcolo variazione percentuale
def variazione_percentuale(df):
    if len(df) < 2:
        return 0
    return round((df["Close"][-1] / df["Close"][-2] - 1) * 100, 2)

# Controllo volatilità vs media
def controllo_anomalia(ticker):
    df = yf.Ticker(ticker).history(period=f"{GIORNI_MEDIA+1}d")
    if len(df) < 2:
        return None
    media = df["Close"][-GIORNI_MEDIA-1:-1].pct_change().abs().mean() * 100
    oggi = variazione_percentuale(df)
    if abs(oggi) >= max(SOGLIA_VOLATILITA, media*2):
        return oggi
    return None

# Controllo notizie
def check_news(keywords):
    feed = feedparser.parse(RSS_FEED)
    alerts = []
    for entry in feed.entries[:5]:  # solo le ultime 5 notizie
        for kw in keywords:
            if kw.lower() in entry.title.lower():
                alerts.append(f"📰 {entry.title}\n{entry.link}")
    return alerts

async def main():
    if not TOKEN or not CHAT_ID:
        raise ValueError("❌ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti")

    bot = Bot(token=TOKEN)

    msg = f"📊 **Alert Mercati – {datetime.now().strftime('%d/%m/%Y')}**\n\n"
    alert_flag = False

    try:
        # BTC, S&P500, Nasdaq
        principali = {"₿ Bitcoin": "BTC-USD", "📈 S&P 500": "^GSPC", "💻 Nasdaq": "^IXIC"}
        for nome, ticker in principali.items():
            val = controllo_anomalia(ticker)
            if val is not None:
                alert_flag = True
                simbolo = "⬆️" if val > 0 else "⬇️"
                msg += f"{nome}: {simbolo} {val}%\n"

        # Azioni minori
        for ticker in TICKER_MINORI:
            val = controllo_anomalia(ticker)
            if val is not None:
                alert_flag = True
                simbolo = "⬆️" if val > 0 else "⬇️"
                msg += f"{ticker}: {simbolo} {val}%\n"

        # Controllo news crypto/mercati
        news_alert = check_news(["bitcoin", "crypto", "market", "indice"])
        if news_alert:
            alert_flag = True
            msg += "\n📌 Notizie rilevanti:\n"
            msg += "\n".join(news_alert)

        if alert_flag:
            await bot.send_message(chat_id=int(CHAT_ID), text=msg)
        else:
            print("Nessun alert oggi – mercati stabili")

    except Exception as e:
        print("Errore durante controllo mercati/notizie:", e)
        # fallback ultra-sicuro: non invia nulla

if __name__ == "__main__":
    asyncio.run(main())
