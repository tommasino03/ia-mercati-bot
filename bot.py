import yfinance as yf
import asyncio
import os
import pandas as pd
from telegram import Bot

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
TICKERS = ["PLTR", "SOFI", "RIVN", "LCID", "UPST", "AFRM", "HOOD"]

CAPITALE_INIT = 10_000
RISCHIO_PERC = 0.01
ATR_MULT = 1.5
MIN_SCORE = 70

# =========================
# INDICATORI
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

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    return tr.rolling(periodi).mean()

# =========================
# SCORE ENTRY
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

    if prezzo > float(close.rolling(20).mean().iloc[i]):
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
    wins = losses = 0
    in_position = False

    atr_series = atr(df)

    for i in range(30, len(df)):
        prezzo = float(df["Close"].iloc[i])

        if not in_position:
            score, supporto = calcola_score(df, i)
            if score >= MIN_SCORE:
                rischio_unit = prezzo - supporto
                if rischio_unit <= 0:
                    continue
                qty = int((capitale * RISCHIO_PERC) / rischio_unit)
                if qty <= 0:
                    continue
                entry = prezzo
                stop = supporto
                in_position = True

        else:
            atr_val = atr_series.iloc[i]
            if pd.isna(atr_val):
                continue
            stop = max(stop, df["High"].iloc[i] - float(atr_val) * ATR_MULT)

            if prezzo <= stop:
                pnl = (prezzo - entry) * qty
                capitale += pnl
                wins += pnl > 0
                losses += pnl <= 0
                in_position = False

        equity_peak = max(equity_peak, capitale)
        max_dd = max(max_dd, (equity_peak - capitale) / equity_peak * 100)

    trades = wins + losses
    if trades == 0:
        return None

    return {
        "ticker": ticker,
        "profitto": round((capitale - CAPITALE_INIT) / CAPITALE_INIT * 100, 2),
        "winrate": round(wins / trades * 100, 1),
        "drawdown": round(max_dd, 2)
    }

# =========================
# RANKING
# =========================
def ranking():
    risultati = []

    for t in TICKERS:
        res = backtest_ticker(t)
        if not res:
            continue

        if res["profitto"] <= 0 or res["winrate"] < 50 or res["drawdown"] > 25:
            continue

        edge = (res["profitto"] * 1.5) + res["winrate"] - (res["drawdown"] * 2)
        res["edge"] = round(edge, 2)
        risultati.append(res)

    return sorted(risultati, key=lambda x: x["edge"], reverse=True)

# =========================
# MAIN
# =========================
async def main():
    ranked = ranking()

    if not ranked:
        await bot.send_message(chat_id=CHAT_ID, text="⚠️ Nessun ticker con edge positivo")
        return

    msg = "🏆 RANKING EDGE STRATEGIA\n\n"
    for r in ranked:
        msg += (
            f"🔹 {r['ticker']}\n"
            f"EDGE: {r['edge']}\n"
            f"Profitto: {r['profitto']}%\n"
            f"Win rate: {r['winrate']}%\n"
            f"Drawdown: {r['drawdown']}%\n\n"
        )

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
