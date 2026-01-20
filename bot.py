import yfinance as yf
import pandas as pd
import numpy as np
import asyncio

# =======================
# CONFIG
# =======================
TICKERS = ["AAPL", "MSFT", "NVDA", "AMD", "META"]
RSI_BUY = 30
RSI_SELL = 70
MIN_EDGE = 10
PERIODO = "6mo"
INTERVALLO = "1d"


# =======================
# UTILS
# =======================
def scalar(x):
    """Forza qualsiasi Series/DataFrame a float puro"""
    return float(x.iloc[-1].item())


# =======================
# INDICATORI
# =======================
def rsi(series, period=14):
    series = series.astype(float)
    delta = series.diff()

    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def atr(df, period=14):
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    close = df["Close"].astype(float)

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    return tr.rolling(period).mean()


# =======================
# TREND MERCATO
# =======================
def trend_index(ticker="^GSPC"):
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if df.empty or len(df) < 50:
        return "NEUTRAL"

    close = df["Close"].astype(float)
    ma50 = close.rolling(50).mean()

    return "UP" if scalar(close) > scalar(ma50) else "DOWN"


# =======================
# EDGE STATISTICO
# =======================
def calcola_edge(ticker):
    df = yf.download(ticker, period=PERIODO, interval=INTERVALLO, progress=False)
    if df.empty or len(df) < 60:
        return None

    close = df["Close"].astype(float)

    start = float(close.iloc[0].item())
    end = scalar(close)

    profitto = (end - start) / start * 100
    drawdown = float(((close.cummax() - close) / close.cummax()).max().item())
    winrate = 55  # proxy conservativo

    edge = (profitto * 1.5) + winrate - (drawdown * 2)
    return round(edge, 2)


# =======================
# ANALISI TICKER
# =======================
def analizza_ticker(ticker):
    df = yf.download(ticker, period=PERIODO, interval=INTERVALLO, progress=False)
    if df.empty or len(df) < 50:
        return None

    close = df["Close"].astype(float)
    volume = df["Volume"].astype(float)

    rsi_val = scalar(rsi(close))
    atr_val = scalar(atr(df))

    vol_last = scalar(volume)
    vol_mean = float(volume.rolling(20).mean().iloc[-1].item())

    volume_spike = vol_last > vol_mean * 1.5

    edge = calcola_edge(ticker)
    if edge is None or edge < MIN_EDGE:
        return None

    if rsi_val <= RSI_BUY and volume_spike:
        signal = "BUY"
    elif rsi_val >= RSI_SELL:
        signal = "SELL"
    else:
        return None

    return {
        "ticker": ticker,
        "signal": signal,
        "rsi": round(rsi_val, 2),
        "atr": round(atr_val, 2),
        "edge": edge
    }


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

    if not risultati:
        print("❌ Nessun segnale valido")
        return

    risultati.sort(key=lambda x: x["edge"], reverse=True)

    print("🔥 SEGNALI TROVATI:\n")
    for r in risultati:
        print(
            f"{r['ticker']} | {r['signal']} | "
            f"RSI: {r['rsi']} | ATR: {r['atr']} | EDGE: {r['edge']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
