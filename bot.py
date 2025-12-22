import yfinance as yf
import requests

# ===== CONFIG =====
TOKEN = "8268985960:AAHqyZ679C4B4y7ICq96xQy5JU9PJ_1KiZg"
CHAT_ID = "595821281"

CAPITALE = 200
INVESTIMENTO_PER_TRADE = 20

# ===== REGIME DI MERCATO =====
def market_regime():
    sp = yf.download("SPY", period="6mo", interval="1d", progress=False)
    nd = yf.download("QQQ", period="6mo", interval="1d", progress=False)

    # Controllo dati sufficienti
    if sp.empty or nd.empty or len(sp) < 50 or len(nd) < 50:
        return "NEUTRO"

    # Prendi singoli float sicuri
    sp_last = sp["Close"].iloc[-1].item()
    nd_last = nd["Close"].iloc[-1].item()

    sp_ma50 = sp["Close"].iloc[-50:].mean().item()
    nd_ma50 = nd["Close"].iloc[-50:].mean().item()

    if sp_last > sp_ma50 and nd_last > nd_ma50:
        return "🟢 RISK-ON"
    elif sp_last < sp_ma50 and nd_last < nd_ma50:
        return "🔴 RISK-OFF"
    else:
        return "🟡 NEUTRO"

REGIME = market_regime()

# ===== ASSET CON FILTRO SMART MONEY =====
assets = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "Nvidia",
    "SPY": "S&P500",
    "QQQ": "Nasdaq",
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum"
}

msg = "🤖 IA MERCATI – REGIME & SEGNALI (Smart Money)\n"
msg += f"Regime mercato: {REGIME}\n\n"

for t, name in assets.items():
    data = yf.download(t, period="6mo", interval="1d", progress=False)
    if data.empty or len(data) < 50:
        continue

    close = data["Close"].values
    last = close[-1].item() if hasattr(close[-1], "item") else float(close[-1])
    ma20 = data["Close"].iloc[-20:].mean().item()
    ma50 = data["Close"].iloc[-50:].mean().item()
    max20 = data["Close"].iloc[-20:].max().item()

    # ===== SCORE BASE =====
    score = 0
    if last > ma20: score += 2
    if last > ma50: score += 3
    if last >= max20: score += 2

    # ===== FILTRO SMART MONEY =====
    vol = data["Volume"].iloc[-5:].mean()
    vol50 = data["Volume"].iloc[-50:].mean()
    smart_money = vol > vol50  # True se volume recente > volume medio a lungo termine

    # ===== DECISIONE FINALE =====
    if REGIME == "🔴 RISK-OFF":
        action = "⛔ BLOCCATO"
        size = "-"
    else:
        if score >= 5 and smart_money:
            action = "✅ COMPRA"
            size = f"{INVESTIMENTO_PER_TRADE} €"
        elif score >= 5 and not smart_money:
            action = "⚠ ATTENDI (volume basso)"
            size = "-"
        else:
            action = "⏳ ATTENDI"
            size = "-"

    msg += f"{name}\nScore: {score}\nAzione: {action}\nImporto: {size}\n\n"

# ===== INVIO MESSAGGIO SU TELEGRAM =====
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
