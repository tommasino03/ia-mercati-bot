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
SOGLIA_VOLATILITA = 2.0      # soglia % minima alert
GIORNI_MEDIA = 5             # giorni per media storica
NUM_TOP_VOL = 10             # top N small-cap
RSS_FEED = "https://www.coindesk.com/arc/outboundfeeds/rss/"
KEYWORDS = ["bitcoin", "crypto", "market", "indice"]

# Funzioni utility
def variazione_percentuale(df):
    if len(df) < 2:
        return 0
    return round((df["Close"][-1] / df["Close"][-2] - 1) * 100, 2)

def controllo_anomalia(ticker):
    df = yf.Ticker(ticker).history(period=f"{GIORNI_MEDIA+1}d")
    if len(df) < 2:
        return None
    media = df["Close"][-GIORNI_MEDIA-1:-1].pct_change().abs().mean() * 100
    oggi = variazione_percentuale(df)
    if abs(oggi) >= max(SOGLIA_VOLATILITA, media*2):
        return oggi
    return None

def check_news():
    feed = feedparser.parse(RSS_FEED)
    alerts = []
    for entry in feed.entries[:5]:
        for kw in KEYWORDS:
            if kw.lower() in entry.title.lower():
                alerts.append(f"📰 {entry.title}\n{entry.link}")
    return alerts

def small_cap_alerts():
    SMALL_CAPS = [
        "PLTR","NIO","RIVN","COIN","LCID","SOFI","AFRM","SNAP","TWLO","FUBO",
        "MARA","HUT","RIOT","ETSY","DDOG","UBER","LYFT","CRWD","DOCU","SQ",
        "GME","AMC","SNDL","KOSS","BB","BARK","ZNGA","SPCE","VYGR","FCEL"
    ]
    vol_dict = {}
    for ticker in SMALL_CAPS:
        val = controllo_anomalia(ticker)
        if val is not None:
            vol_dict[ticker] = val
    # Ordina per valore assoluto e prendi top-N
    top_vol = dict(sorted(vol_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:NUM_TOP_VOL])
    return top_vol

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

def correlazione_btc_smallcap(btc_val, small_alerts):
    if btc_val is None or not small_alerts:
        return None
    trend_btc = 1 if btc_val>0 else -1
    trend_small = [1 if v>0 else -1 for v in small_alerts.values()]
    same_trend = sum(1 for t in trend_small if t==trend_btc)
    percentuale = same_trend / len(trend_small) * 100
    if percentuale >= 60:  # se almeno 60% small-cap segue BTC
        direzione = "rialzista" if trend_btc>0 else "ribassista"
        return f"⚡ BTC {direzione} e {int(percentuale)}% delle small-cap seguono lo stesso trend"
    return None

async def main():
    if not TOKEN or not CHAT_ID:
        raise ValueError("❌ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti")

    bot = Bot(token=TOKEN)
    msg = f"📊 **Alert Mercati – {datetime.now().strftime('%d/%m/%Y')}**\n\n"
    alert_flag = False

    try:
        # Principali
        principali = {"₿ Bitcoin":"BTC-USD","📈 S&P 500":"^GSPC","💻 Nasdaq":"^IXIC"}
        btc_val = None
        for nome, ticker in principali.items():
            val = controllo_anomalia(ticker)
            if nome=="₿ Bitcoin":
                btc_val = val
            if val is not None:
                alert_flag = True
                simbolo = "⬆️" if val>0 else "⬇️"
                msg += f"{nome}: {simbolo} {val}%\n"

        # Small-cap
        small_alert = small_cap_alerts()
        if small_alert:
            alert_flag = True
            for t, v in small_alert.items():
                simbolo = "⬆️" if v>0 else "⬇️"
                msg += f"{t}: {simbolo} {v}%\n"
            grafico = crea_grafico_small_cap(small_alert)
        else:
            grafico = None

        # Correlazione BTC ↔ small-cap
        corr_msg = correlazione_btc_smallcap(btc_val, small_alert)
        if corr_msg:
            alert_flag = True
            msg += f"\n{corr_msg}\n"

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
        print("Errore durante controllo mercati/notizie/grafico/correlazione:", e)

if __name__=="__main__":
    asyncio.run(main())
