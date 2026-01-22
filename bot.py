import os
import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import Bot

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("Token Telegram mancanti")

bot = Bot(token=TOKEN)

CAPITAL = 10_000
RISK_PER_TRADE = 0.01
RISK_REWARD = 2.0
MIN_EDGE = 0.55

TICKERS = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "TSLA",
    "NVDA", "META", "AMD", "PLTR", "ROKU",
    "SOFI", "AFRM", "LCID", "MARA", "RIOT"
]

# ======================
# UTILS
# ======================
def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def scalar(x):
    if isinstance(x, (pd.Series, pd.DataFrame)):
        if len(x) == 0:
            return None
        return float(np.array(x).flatten()[-1])
    return float(x)

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ======================
# EDGE BACKTEST
# ======================
def edge_filter(close, ma20):
    wins = 0
    trades = 0
    for i in range(30, len(close) - 5):
        if close.iloc[i] > ma20.iloc[i]:
            trades += 1
            if close.iloc[i + 5] > close.iloc[i]:
                wins += 1
    if trades == 0:
        return 0
    return wins / trades

# ======================
# ANALISI TITOLO
# ======================
def analyze(ticker):
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if df.empty or len(df) < 80:
        return None

    df = clean_df(df)
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    atr = (high - low).rolling(14).mean()
    rsi_val = scalar(rsi(close))

    # === EDGE FILTER ===
    edge = edge_filter(close, ma20)
    if edge < MIN_EDGE:
        return None

    # === ANOMALIA VOLUMI ===
    vol_mean = volume.rolling(20).mean()
    vol_spike = scalar(volume) > scalar(vol_mean) * 1.5
    if not vol_spike:
        return None

    last_close = scalar(close)
    last_atr = scalar(atr)

    if last_close <= scalar(ma20) or last_close <= scalar(ma50):
        return None

    # === CLASSIFICAZIONE TRADE ===
    if edge > 0.70 and rsi_val < 40:
        grade = "A+"
    elif edge > 0.60:
        grade = "A"
    else:
        grade = "B"

    position_size = int((CAPITAL * RISK_PER_TRADE) / last_atr)
    if position_size <= 0:
        return None

    return {
        "ticker": ticker,
        "entry": round(last_close, 2),
        "stop": round(last_close - last_atr, 2),
        "target": round(last_close + last_atr * RISK_REWARD, 2),
        "size": position_size,
        "edge": round(edge * 100, 1),
        "rsi": round(rsi_val, 1),
        "grade": grade
    }

# ======================
# MAIN
# ======================
async def main():
    trades = []

    for t in TICKERS:
        res = analyze(t)
        if res:
            trades.append(res)

    if not trades:
        await bot.send_message(
            chat_id=CHAT_ID,
            text="📭 Nessuna opportunità con edge reale oggi"
        )
        return

    # === STATISTICHE GIORNALIERE ===
    total_trades = len(trades)
    avg_edge = round(sum(t['edge'] for t in trades) / total_trades, 1)
    avg_rsi = round(sum(t['rsi'] for t in trades) / total_trades, 1)

    # === TRADE PRIORITARIO ===
    best_trade = sorted(trades, key=lambda x: x["edge"], reverse=True)[0]

    msg = (
        f"🔥 **TRADE AD ALTA PROBABILITÀ**\n\n"
        f"{best_trade['ticker']} ({best_trade['grade']})\n"
        f"Entry: {best_trade['entry']}\n"
        f"Stop: {best_trade['stop']}\n"
        f"Target: {best_trade['target']}\n"
        f"Size: {best_trade['size']}\n"
        f"Edge: {best_trade['edge']}%\n"
        f"RSI: {best_trade['rsi']}\n\n"
        f"📊 Totale segnali oggi: {total_trades}\n"
        f"📊 Edge medio: {avg_edge}%\n"
        f"📊 RSI medio: {avg_rsi}\n"
        "\n⚠️ Trade filtrato per edge + volumi anomali"
    )

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
