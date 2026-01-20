import os
import asyncio
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from telegram import Bot, InputFile

# =======================
# CONFIGURAZIONE
# =======================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti")

bot = Bot(token=TELEGRAM_TOKEN)

TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
SMALL_CAPS = ["PLTR", "FUBO", "ROKU", "SNAP", "ZM"]
RSI_BUY = 30
RSI_SELL = 70
VOL_THRESHOLD = 2
PERC_THRESHOLD = 5
MIN_EDGE = 5

# =======================
# FUNZIONI UTILI
# =======================
def scalar(series):
    return float(series.iloc[-1])

def calcola_edge(ticker):
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if df.empty or len(df) < 60:
        return None

    close = df["Close"].astype(float)
    start = float(close.iloc[0])
    end = float(close.iloc[-1])

    profitto = (end - start) / start * 100
    winrate = 55
    drawdown = ((close.cummax() - close) / close.cummax()).max() * 100
    edge = (profitto * 1.5) + winrate - (drawdown * 2)
    return round(float(edge), 2)

def rsi(df, period=14):
    delta = df["Close"].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(period).mean()
    ma_down = down.rolling(period).mean()
    rs = ma_up / ma_down
    rsi = 100 - (100 / (1 + rs))
    return rsi

def atr(df, period=14):
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr

def analizza_ticker(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    if df.empty or len(df) < 20:
        return None

    close = df["Close"].astype(float)
    volume = df["Volume"].astype(float)
    last_close = scalar(close)
    ma50 = close.rolling(50).mean()
    last_ma50 = float(ma50.iloc[-1])
    rsi_val = float(rsi(df).iloc[-1])
    atr_val = float(atr(df).iloc[-1])
    vol_last = scalar(volume)
    vol_mean = float(volume.rolling(20).mean().iloc[-1])
    volume_spike = vol_last > vol_mean * VOL_THRESHOLD
    edge = calcola_edge(ticker)

    signal = None
    if last_close > last_ma50 and rsi_val < RSI_BUY and volume_spike:
        signal = "BUY"
    elif last_close < last_ma50 and rsi_val > RSI_SELL and volume_spike:
        signal = "SELL"

    if signal:
        return {"ticker": ticker, "signal": signal, "rsi": round(rsi_val,2),
                "atr": round(atr_val,2), "edge": edge, "df": df}
    return None

def analizza_small_cap(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    if df.empty or len(df) < 20:
        return None

    close = df["Close"].astype(float)
    volume = df["Volume"].astype(float)

    perc_move = (scalar(close) - float(close.iloc[-2])) / float(close.iloc[-2]) * 100
    vol_last = scalar(volume)
    vol_mean = float(volume.rolling(20).mean().iloc[-1])
    volume_spike = vol_last > vol_mean * VOL_THRESHOLD

    if abs(perc_move) >= PERC_THRESHOLD or volume_spike:
        signal = "MOVIMENTO ALTO"
        return {
            "ticker": ticker,
            "signal": signal,
            "perc_move": round(perc_move, 2),
            "vol_ratio": round(vol_last / vol_mean, 2),
            "df": df
        }
    return None

def trend_index():
    sp500 = yf.download("^GSPC", period="3mo", interval="1d", progress=False)
    if sp500.empty or len(sp500) < 50:
        return "UNKNOWN"
    last = float(sp500["Close"].iloc[-1])
    ma50 = float(sp500["Close"].rolling(50).mean().iloc[-1])
    return "UP" if last > ma50 else "DOWN"

def crea_grafico(ticker, df, segnale):
    plt.figure(figsize=(8,4))
    plt.plot(df["Close"], label="Close")
    plt.title(f"{ticker} | {segnale}")
    plt.xlabel("Data")
    plt.ylabel("Prezzo")
    plt.grid(True)
    plt.legend()
    filename = f"{ticker}_grafico.png"
    plt.savefig(filename)
    plt.close()
    return filename

# =======================
# MAIN
# =======================
async def main():
    mercato = trend_index()
    print(f"\n📊 Trend mercato: {mercato}\n")

    risultati = []

    for t in TICKERS:
        res = analizza_ticker(t)
        if res:
            risultati.append(res)

    for t in SMALL_CAPS:
        res = analizza_small_cap(t)
        if res:
            risultati.append(res)

    if not risultati:
        print("❌ Nessun segnale valido")
        return

    # Ranking per EDGE o perc_move
    risultati.sort(key=lambda x: x.get("edge", abs(x.get("perc_move", 0))), reverse=True)

    messaggio = f"🔥 SEGNALI TROVATI ({len(risultati)} titoli):\n"
    for r in risultati:
        if "edge" in r:
            messaggio += f"{r['ticker']} | {r['signal']} | RSI: {r['rsi']} | ATR: {r['atr']} | EDGE: {r['edge']}\n"
        else:
            messaggio += f"{r['ticker']} | {r['signal']} | % Move: {r['perc_move']}% | Vol ratio: {r['vol_ratio']}\n"

    print(messaggio)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=messaggio)

    # Invia grafici
    for r in risultati:
        grafico = crea_grafico(r["ticker"], r["df"], r["signal"])
        with open(grafico, "rb") as f:
            await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=InputFile(f))
        os.remove(grafico)

if __name__ == "__main__":
    asyncio.run(main())
