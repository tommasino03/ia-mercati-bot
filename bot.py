import yfinance as yf
import requests

TOKEN = "8268985960:AAHqyZ679C4B4y7ICq96xQy5JU9PJ_1KiZg"
CHAT_ID = "595821281"

CAPITALE = 200
INVESTIMENTO_PER_TRADE = 20

assets = {
    "AAPL": "Apple (azione)",
    "MSFT": "Microsoft (azione)",
    "NVDA": "Nvidia (azione)",
    "SPY": "S&P500 (ETF)",
    "QQQ": "Nasdaq (ETF)",
    "BTC-USD": "Bitcoin (crypto)",
    "ETH-USD": "Ethereum (crypto)"
}

msg = "🤖 IA MERCATI – SEGNALI OPERATIVI\n"
msg += f"Capitale test: {CAPITALE} €\n\n"

for t, name in assets.items():
    data = yf.download(t, period="6mo", interval="1d", progress=False)
    if data is None or len(data) < 50:
        continue

    close = data["Close"].values
    last = close[-1]
    ma20 = close[-20:].mean()
    ma50 = close[-50:].mean()
    max20 = max(close[-20:])

    score = 0
    reasons = []

    if last > ma20:
        score += 2
        reasons.append("sopra media 20g")
    if last > ma50:
        score += 3
        reasons.append("trend positivo")
    if last >= max20:
        score += 2
        reasons.append("massimi recenti")

    if score >= 5:
        action = "✅ COMPRA"
        size = f"{INVESTIMENTO_PER_TRADE} €"
    else:
        action = "⏳ ATTENDI"
        size = "-"

    msg += f"🔹 {name}\n"
    msg += f"Score: {score}\n"
    msg += f"Azione: {action}\n"
    msg += f"Importo: {size}\n"
    msg += f"Motivo: {', '.join(reasons) if reasons else 'debole'}\n\n"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
