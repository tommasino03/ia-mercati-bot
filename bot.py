import yfinance as yf
import requests

TOKEN = "8268985960:AAHqyZ679C4B4y7ICq96xQy5JU9PJ_1KiZg"
CHAT_ID = "595821281"

CAPITALE = 200
INVESTIMENTO_PER_TRADE = 20

# ===== REGIME DI MERCATO =====
def market_regime():
    sp = yf.download("SPY", period="6mo", interval="1d", progress=False)
    nd = yf.download("QQQ", period="6mo", interval="1d", progress=False)

    if len(sp) < 50 or len(nd) < 50:
        return "NEUTRO"

    sp_last = sp["Close"].iloc[-1]
    nd_last = nd["Close"].iloc[-1]

    sp_ma50 = sp["Close"].iloc[-50:].mean()
    nd_ma50 = nd["Close"].iloc[-50:].mean()

    if sp_last > sp_ma50 and nd_last > nd_ma50:
        return "🟢 RISK-ON"
    elif sp_last < sp_ma50 and nd_last < nd_ma50:
        return "🔴 RISK-OFF"
    else:
        return "🟡 NEUTRO"

REGIME = market_regime()

# ===== ASSET =====
assets = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "Nvidia",
    "SPY": "S&P500",
    "QQQ": "Nasdaq",
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum"
}

msg = "🤖 IA MERCATI – REGIME & SEGNALI\n"
msg += f"Regime mercato: {REGIME}\n\n"

for t, name in assets.items():
    data = yf.download(t, period="6mo", interval="1d", progress=False)
    if len(data) < 50:
        continue

    close = data["Close"].values
    last = close[-1]
    ma20 = close[-20:].mean()
    ma50 = close[-50:].mean()
    max20 = max(close[-20:])

    score = 0
    if last > ma20: score += 2
    if last > ma50: score += 3
    if last >= max20: score += 2

    if REGIME == "🔴 RISK-OFF":
        action = "⛔ BLOCCATO"
        size = "-"
    else:
        action = "✅ COMPRA" if score >= 5 else "⏳ ATTENDI"
        size = f"{INVESTIMENTO_PER_TRADE} €" if action == "✅ COMPRA" else "-"

    msg += f"{name}\nScore: {score}\nAzione: {action}\nImporto: {size}\n\n"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
