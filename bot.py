import os
import yfinance as yf
from telegram import Bot
from datetime import datetime

# ======================
# CONFIG
# ======================
ASSETS = {
    "Azioni USA": ["AAPL", "GOOGL", "META", "TSLA", "JPM"],
    "ETF": ["SPY", "QQQ"],
    "Azioni Europa": ["SAN.MC"]
}

# ======================
# UTILS
# ======================
def get_env():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    if not token or not chat_id:
        raise ValueError("Token o Chat ID mancanti")
    return token, chat_id


def trend_label(short, mid, long):
    if short == "BUY" and mid == "BUY" and long == "BUY":
        return "🔥 TREND FORTE"
    if short != "BUY" and mid == "BUY" and long == "BUY":
        return "🟡 ACCUMULO"
    if short == "SELL" and mid == "SELL":
        return "🔴 DEBOLE"
    return "⚪ LATERALE"


def analyze_asset(ticker):
    data = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if data.empty:
        return None

    close = data["Close"]

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()

    short = "BUY" if close.iloc[-1] > ma20.iloc[-1] else "NEUTRAL"
    mid = "BUY" if close.iloc[-1] > ma50.iloc[-1] else "NEUTRAL"
    long = "BUY" if close.iloc[-1] > ma200.iloc[-1] else "NEUTRAL"

    strength = trend_label(short, mid, long)

    return {
        "short": short,
        "mid": mid,
        "long": long,
        "strength": strength
    }


# ======================
# MAIN
# ======================
def main():
    token, chat_id = get_env()
    bot = Bot(token=token)

    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    message = f"📊 REPORT IA MERCATI – {now}\n\n"

    opportunita = []
    monitorare = []
    evitare = []

    for category, tickers in ASSETS.items():
        message += f"--- {category} ---\n"
        for t in tickers:
            res = analyze_asset(t)
            if not res:
                continue

            message += (
                f"📌 {t}\n"
                f"Breve: {res['short']}\n"
                f"Medio: {res['mid']}\n"
                f"Lungo: {res['long']}\n"
                f"Stato: {res['strength']}\n\n"
            )

            if res["strength"] == "🔥 TREND FORTE":
                opportunita.append(t)
            elif res["strength"] == "🟡 ACCUMULO":
                monitorare.append(t)
            elif res["strength"] == "🔴 DEBOLE":
                evitare.append(t)

    # ======================
    # SINTESI INTELLIGENTE
    # ======================
    message += "🧠 SINTESI OPERATIVA\n"

    if opportunita:
        message += f"🎯 Opportunità: {', '.join(opportunita)}\n"
    if monitorare:
        message += f"👀 Da monitorare: {', '.join(monitorare)}\n"
    if evitare:
        message += f"🛑 Deboli: {', '.join(evitate for evitate in evitare)}\n"

    if opportunita:
        strategy = "Trend positivo → investire gradualmente"
        risk = "MEDIO"
    else:
        strategy = "Attendere conferme"
        risk = "BASSO"

    message += f"\nStrategia: {strategy}\nRischio: {risk}"

    bot.send_message(chat_id=chat_id, text=message)


if __name__ == "__main__":
    main()
