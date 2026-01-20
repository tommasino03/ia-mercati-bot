import yfinance as yf
import asyncio
import os
from telegram import Bot
import pandas as pd

# =========================
# ENV
# =========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("❌ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti")

bot = Bot(token=TOKEN)

# =========================
# CONFIG
# =========================
TICKERS = ["PLTR", "SOFI", "RIVN", "LCID", "UPST"]

CAPITALE_INIT = 10_000
RISCHIO_PERC = 0.01
ATR_MULT = 1.5
MIN_SCORE = 70

# =========================
# INDICATORI SICURI
# =========================
def rsi(close, periodi=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(periodi).mean()
    loss = -delta.where(delta < 0, 0.0).rolling(periodi).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def atr(df, periodi=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(periodi).mean()

# =========================
# SCORE
# =========================
def calcola_score(df, i):
    close = df["Close"]
    low = df["Low"]
    high = df["High"]

    prezzo = float(close.iloc[i])
    r = float(rsi(close).iloc[i])

    score = 0

    if 25 <= r <= 45:
        score += 25

    ma20 = float(close.rolling(20).mean().iloc[i])
    if prezzo > ma20:
        score += 20

    supporto = float(low.iloc[i-10:i].min())
    resistenza = float(high.iloc[i-10:i].max())

    if (resistenza - prezzo) > (prezzo - supporto) * 2:
        score += 25

    return score, supporto

# =========================
# BACKTEST
# =========================
def backtest_ticker(ticker):
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)

    if df.empty or len(df) < 60:
        return None

    capitale = CAPITALE_INIT
    equity_peak = CAPITALE_INIT
    max_dd = 0
    wins = 0
    losses = 0

    in_position = False
    entry = stop = qty = 0

    atr_series = atr(df)

    for i in range(30, len(df)):
        prezzo = float(df["Close"].iloc[i])

        if not in_position:
            score, supporto = calcola_score(df, i)

            if score >= MIN_SCORE:
                rischio = capitale * RISCHIO_PERC
                stop = supporto
                rischio_unit = prezzo - stop

                if rischio_unit <= 0:
                    continue

                qty = int(rischio / rischio_unit)
                if qty <= 0:
                    continue

                entry = prezzo
                in_position = True

        else:
            atr_val = atr_series.iloc[i]
            if pd.isna(atr_val):
                continue

            atr_val = float(atr_val)
            stop = max(stop, df["High"].iloc[i] - atr_val * ATR_MULT)

            if prezzo <= stop:
                pnl = (prezzo - entry) * qty
                capitale += pnl

                if pnl > 0:
                    wins += 1
                else:
                    losses += 1

                in_position = False

        equity_peak = max(equity_peak, capitale)
        dd = (equity_peak - capitale) / equity_peak * 100
        max_dd = max(max_dd, dd)

    trade_tot = wins + losses
    if trade_tot == 0:
        return None

    rendimento = (capitale - CAPITALE_INIT) / CAPITALE_INIT * 100
    winrate = wins / trade_tot * 100

    return {
        "ticker": ticker,
        "trades": trade_tot,
        "winrate": round(winrate, 1),
        "profitto": round(rendimento, 2),
        "drawdown": round(max_dd, 2)
    }

# =========================
# MAIN
# =========================
async def main():
    msg = "📈 BACKTEST STRATEGIA (6 MESI)\n\n"

    for t in TICKERS:
        res = backtest_ticker(t)
        if not res:
            continue

        msg += (
            f"🔹 {res['ticker']}\n"
            f"Trades: {res['trades']}\n"
            f"Win rate: {res['winrate']}%\n"
            f"Profitto: {res['profitto']}%\n"
            f"Max DD: {res['drawdown']}%\n\n"
        )

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
