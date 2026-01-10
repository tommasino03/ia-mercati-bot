import os
import asyncio
from datetime import datetime
from telegram import Bot
import yfinance as yf
import feedparser
import matplotlib.pyplot as plt

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print("TOKEN:", "OK" if TOKEN else "MANCANTE")
print("CHAT_ID:", "OK" if CHAT_ID else "MANCANTE")

# Configurazioni
SOGLIA_VOLATILITA = 2.0      # soglia minima % alert
GIORNI_MEDIA = 5             # giorni per calcolare media storica
NUM_TOP_VOL = 10             # quante small-cap più volatili considerare
RSS_FEED = "https://www.coindesk.com/arc/outboundfeeds/rss/"
KEYWORDS = ["bitcoin", "crypto", "market", "indice"]

# Funzione variazione %
def variazione_percentuale(df):
    if len(df) < 2:
        return 0
    return round((df["Close"][-1] / df["Close"][-2] - 1) * 100, 2)

# Controllo anomalia rispetto media storica
def controllo_anomalia(ticker):
    df = yf.Ticker(ticker).history(period=f"{GIORNI_MEDIA+1}d")
    if len(df) < 2:
        return None
    media = df["Close"][-GIORNI_MEDIA-1:-1].pct_change().abs().mean() * 100
    oggi = variazione_percentuale(df)
    if abs(oggi) >= max(SOGLIA_VOLATILITA, media*2):
        return oggi
    return None

# Controllo notizie RSS
def check_news():
    feed = feedparser.parse(RSS_FEED)
    alerts = []
    for entry in feed.entries[:5]:
        for kw in KEYWORDS:
            if kw.lower() in entry.title.lower():
                alerts.append(f"📰 {entry.title}\n{entry.link}")
    return alerts

# Small-cap automatiche: selezione top-N più volatili
def small_cap_alerts():
    # Lista esempio di small-cap US (puoi usare ETF Russell 2000)
    SMALL_CAPS = [
        "PLTR","NIO","RIVN","COIN","LCID","SOFI","AFRM","SNAP","TWLO","FUBO",
        "MARA","HUT","RIOT","ETSY","DDOG","UBER","LYFT","CRWD","DOCU","SQ",
        "GME","AMC","SNDL","KOSS","BB","BARK","ZNGA","SPCE","VYGR","FCEL"
    ]
    # Calcolo variazioni odierne
    vol_dict = {}
    for ticker in SMALL_CAPS:
        val = controllo_anomalia(ticker)
        if val is not None:
            vol_dict[ticker] = val
    # Ordina per valore assoluto e prendi top-N
    top_vol = dict(sorted(vol_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:NUM_TOP_VOL])
    return top_vol

# Crea grafico small-cap
def crea_grafico_small_cap(alerts):
    tickers = list(alerts.keys())
    valori = [alerts[t] for t in tickers]
    plt.figure(figsize=(10,6))
    bars = plt.bar(tickers, valori, color=['green' if v>0 else 'red' for v in valori])
    plt.axhline(0, color='black', linewidth=0.8)
    plt.ylabel("Variazione %")
    plt.title("Top Small-cap più volatili oggi")
    for bar, val in zip(bars, valori):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height + (0.2 if height>0 else -0.7),
                 f"{val}%", ha='center', color='black', fontsize=9)
    file_png = "/tmp/smallcap_alert.png"
    plt.tight_layout()
    plt.savefig(file_png)
    plt.close()
    return file_png

async def main():
    if not TOKEN or not CHAT_ID:
        raise ValueError("❌ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti")

    bot = Bot(token=TOKEN)
    msg = f"📊 **Alert Mercati – {datetime.now().strftime('%d/%m/%Y')}**\n\n"
    alert_flag = False

    try:
        # Principali
        principali = {"₿ Bitcoin":"BTC-USD","📈 S&P 500":"^GSPC","💻 Nasdaq":"^IXIC"}
        for nome, ticker in principali.items():
            val = controllo_anomalia(ticker)
            if val is not None:
                alert_flag = True
                simbolo = "⬆️" if val>0 else "⬇️"
                msg += f"{nome}: {simbolo} {val}%\n"

        # Small-cap automatiche
        small_alert = small_cap_alerts()
        if small_alert:
            alert_flag = True
            for t, v in small_alert.items():
                simbolo = "⬆️" if v>0 else "⬇️"
                msg += f"{t}: {simbolo} {v}%\n"
            grafico = crea_grafico_small_cap(small_alert)
        else:
            grafico = None

        # Notizie
        news_alert = check_news()
        if news_alert:
            alert_flag = True
            msg += "\n📌 Notizie rilevanti:\n" + "\n".join(news_alert)

        # Invia messaggio
        if alert_flag:
            if grafico:
                await bot.send_photo(chat_id=int(CHAT_ID), photo=open(grafico,'rb'), caption=msg)
            else:
                await bot.send_message(chat_id=int(CHAT_ID), text=msg)
        else:
            print("Nessun alert oggi – mercati stabili")

    except Exception as e:
        print("Errore durante controllo mercati/notizie/grafico:", e)

if __name__=="__main__":
    asyncio.run(main())
