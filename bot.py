import os
import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import Bot
from datetime import datetime, timedelta

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("Token Telegram mancanti")

bot = Bot(token=TOKEN)

CAPITALE_INIZIALE = 1000
RISK_PER_TRADE = 0.02
RISK_REWARD = 2.0
TRADES_FILE = "trades.csv"

TICKERS = [
    "AAPL","MSFT","NVDA","AMD","META","AMZN","TSLA",
    "PLTR","COIN","RIVN","SOFI","AFRM","SHOP","UBER",
    "SNAP","PYPL","ROKU","MARA","RIOT"
]

# ======================
# UTILS ROBUSTI
# ======================
def safe_last(x):
    try:
        if isinstance(x, pd.DataFrame):
            x = x.iloc[:, 0]
        if isinstance(x, pd.Series):
            x = x.dropna()
            if len(x) == 0:
                return None
            return float(x.iloc[-1])
        return float(x)
    except:
        return None

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ======================
# STORAGE
# ======================
def load_trades():
    if not os.path.exists(TRADES_FILE):
        return pd.DataFrame()
    return pd.read_csv(TRADES_FILE)

def save_trade(trade):
    df = load_trades()
    df = pd.concat([df, pd.DataFrame([trade])], ignore_index=True)
    df.to_csv(TRADES_FILE, index=False)

# ======================
# TREND MERCATO
# ======================
def market_trend():
    df = yf.download("^GSPC", period="1y", interval="1d", progress=False)
    if df.empty or len(df) < 60:
        return "NEUTRAL"

    close = df["Close"]
    ma50 = safe_last(close.rolling(50).mean())
    ma200 = safe_last(close.rolling(200).mean())

    if ma50 is None or ma200 is None:
        return "NEUTRAL"
    if ma50 > ma200:
        return "UP"
    elif ma50 < ma200:
        return "DOWN"
    return "NEUTRAL"

# ======================
# ANALISI TITOLO NEXT LEVEL
# ======================
def analyze_ticker(ticker, trend, capitale):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    if df.empty or len(df) < 30:
        return None

    df = df.dropna()
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    price = safe_last(close)
    prev = safe_last(close.shift(1))
    if price is None or prev is None:
        return None

    daily_change = ((price - prev) / prev) * 100

    # Filtro movers reali
    vol_avg = safe_last(volume.rolling(20).mean())
    vol_now = safe_last(volume)
    if vol_avg is None or vol_now is None:
        return None
    if vol_now < vol_avg * 1.5:
        return None
    if daily_change < 3:
        return None

    # Solo trend positivo
    if trend != "UP":
        return None

    # Indicatori tecnici
    rsi_val = safe_last(rsi(close))
    ma20 = safe_last(close.rolling(20).mean())
    ma50 = safe_last(close.rolling(50).mean())
    atr = safe_last((high - low).rolling(14).mean())
    if None in [rsi_val, ma20, ma50, atr] or atr <= 0:
        return None
    if not (price > ma20 > ma50) or rsi_val > 60:
        return None

    # Calcolo size
    risk = capitale * RISK_PER_TRADE
    stop = price - atr
    size = max(1, int(risk / (price - stop)))

    return {
        "ticker": ticker,
        "entry": round(price,2),
        "stop": round(stop,2),
        "target": round(price + atr * RISK_REWARD,2),
        "size": size,
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "status": "OPEN",
        "reason": f"Breakout + volume | +{round(daily_change,1)}% | RSI {round(rsi_val,1)}"
    }

# ======================
# TRACCIAMENTO AUTOMATICO
# ======================
async def check_trades():
    df = load_trades()
    capitale = CAPITALE_INIZIALE
    if df.empty:
        return capitale

    for i, row in df.iterrows():
        if row["status"] != "OPEN":
            capitale += row.get("pnl",0)
            continue

        data = yf.download(row["ticker"], period="5d", interval="1d", progress=False)
        if data.empty:
            continue
        price = safe_last(data["Close"])
        if price is None:
            continue

        pnl = 0
        if price >= row["target"]:
            pnl = (row["target"] - row["entry"])*row["size"]
            df.loc[i,"status"] = "WIN"
        elif price <= row["stop"]:
            pnl = (row["stop"] - row["entry"])*row["size"]
            df.loc[i,"status"] = "LOSS"

        if pnl != 0:
            df.loc[i,"exit_price"] = price
            df.loc[i,"pnl"] = round(pnl,2)
            await bot.send_message(
                chat_id=CHAT_ID,
                text=f"🔔 CHIUSURA {row['ticker']}\nRisultato: {df.loc[i,'status']}\nPNL: {round(pnl,2)}€"
            )

    df.to_csv(TRADES_FILE,index=False)
    return capitale

# ======================
# MAIN
# ======================
async def main():
    capitale = await check_trades()
    trend = market_trend()
    nuovi = []

    for t in TICKERS:
        trade = analyze_ticker(t, trend, capitale)
        if trade:
            save_trade(trade)
            nuovi.append(trade)

    if not nuovi:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"📭 Nessun trade oggi\nTrend: {trend}\nCapitale: {round(capitale,2)}€"
        )
        return

    msg = f"🚀 NUOVI TRADE (Paper)\nTrend: {trend}\nCapitale: {round(capitale,2)}€\n\n"
    for t in nuovi:
        msg += (
            f"📌 {t['ticker']}\n"
            f"Motivo: {t['reason']}\n"
            f"Entry: {t['entry']}\n"
            f"Stop: {t['stop']}\n"
            f"Target: {t['target']}\n"
            f"Size: {t['size']}\n\n"
        )
    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
