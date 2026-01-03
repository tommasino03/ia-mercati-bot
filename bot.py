import os
import asyncio
from datetime import datetime
import yfinance as yf
import pandas as pd
from fpdf import FPDF
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ASSETS = {
    "Azioni USA": ["AAPL","AMZN","GOOGL","META","TSLA","NVDA","JPM","BAC","V","MA","ADBE","CSCO","CMCSA","WMT"],
    "ETF": ["SPY","QQQ","VEA","VGK","IWV","VTI","EFA","IEMG"],
    "Azioni Europa": ["SAN.MC"]
}

# ---------------------- Trend & Score ----------------------
def calculate_trend(close: pd.Series):
    close = close.dropna()
    if len(close) < 60:
        return "⚠️ neutro","⚠️ neutro","⚠️ neutro"
    last = float(close.iloc[-1])
    ema20 = float(close.ewm(span=20).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])
    ema200 = float(close.ewm(span=200).mean().iloc[-1])
    breve = "✅ COMPRA" if last > ema20 else "⚠️ neutro"
    medio = "✅ COMPRA" if ema20 > ema50 else "⚠️ neutro"
    lungo = "✅ INVESTI" if ema50 > ema200 else "⚠️ neutro"
    return breve, medio, lungo

def calculate_score(trend_tuple):
    score=0
    breve, medio, lungo = trend_tuple
    score += 1 if breve=="✅ COMPRA" else 0
    score += 1 if medio=="✅ COMPRA" else 0
    score += 1 if lungo=="✅ INVESTI" else 0
    return score

def analyze_symbol(symbol:str, prev_state:dict):
    data = yf.download(symbol, period="1y", interval="1d", progress=False)
    if data.empty or "Close" not in data: 
        return None, None, None
    trend = calculate_trend(data["Close"])
    score = calculate_score(trend)
    current_state = {"breve":trend[0],"medio":trend[1],"lungo":trend[2],"score":score}
    if prev_state.get(symbol) == current_state: 
        return None, None, None
    msg = f"📌 {symbol}\nBreve: {trend[0]}\nMedio: {trend[1]}\nLungo: {trend[2]}\nScore: {score}/3\n\n"
    return symbol, current_state, msg

# ---------------------- PDF ----------------------
def generate_pdf(report:str, ranking:list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",16)
    pdf.multi_cell(0,8,report)
    pdf.ln(10)
    pdf.set_font("Arial","B",14)
    pdf.cell(0,8,"--- TOP 5 ASSETS ---\n", ln=True)
    pdf.set_font("Arial","",12)
    for sym, score in ranking:
        pdf.cell(0,6,f"{sym} → Score: {score}/3", ln=True)
    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    pdf.output(filename)
    return filename

# ---------------------- State ----------------------
STATE_FILE = "state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        import json
        with open(STATE_FILE,"r") as f:
            return json.load(f)
    return {}

def save_state(state:dict):
    import json
    with open(STATE_FILE,"w") as f:
        json.dump(state,f)

# ---------------------- Main ----------------------
async def main():
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError("BOT_TOKEN o CHAT_ID mancanti")
    bot = Bot(token=BOT_TOKEN)
    state = load_state()
    new_state = state.copy()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 ALERT IA MERCATI – {now}\n\n"
    changed = False
    ranking = []
    
    for section, symbols in ASSETS.items():
        section_text = ""
        for s in symbols:
            result = analyze_symbol(s, state)
            if result and result[0]:
                symbol, current, msg = result
                new_state[symbol] = current
                section_text += msg
                changed = True
                ranking.append((symbol, current["score"]))
        if section_text:
            report += f"--- {section} ---\n{section_text}"
    
    if ranking:
        ranking_sorted = sorted(ranking, key=lambda x: x[1], reverse=True)[:5]
        report += "--- TOP 5 ASSETS DEL GIORNO ---\n"
        for sym, score in ranking_sorted:
            report += f"📌 {sym} → Score: {score}/3\n"
    
    if changed:
        pdf_file = generate_pdf(report, ranking_sorted)
        await bot.send_message(chat_id=CHAT_ID, text=report)
        with open(pdf_file, "rb") as f:
            await bot.send_document(chat_id=CHAT_ID, document=f)
        save_state(new_state)

if __name__ == "__main__":
    asyncio.run(main())
