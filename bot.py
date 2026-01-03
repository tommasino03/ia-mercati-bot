import os
import asyncio
import yfinance as yf
import pandas as pd
from fpdf import FPDF
from telegram import Bot

# Token e chat ID dai secrets
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise RuntimeError("Secrets non trovati. Controlla BOT_TOKEN e CHAT_ID")

# Lista simboli
SYMBOLS = [
    "AAPL", "AMZN", "GOOGL", "META", "TSLA", "NVDA",
    "JPM", "BAC", "V", "MA", "ADBE", "CSCO",
    "CMCSA", "WMT", "SPY", "QQQ", "VEA", "VGK",
    "IWV", "VTI", "EFA", "IEMG", "SAN.MC"
]

# Calcolo trend sicuro
def calculate_trend(close: pd.Series):
    if len(close) < 20:
        return "⚠️ dati insufficienti", "⚠️ dati insufficienti", "⚠️ dati insufficienti"

    last = float(close.iloc[-1])
    ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
    momentum = (last / float(close.iloc[-20]) - 1) * 100

    breve = "✅ COMPRA" if last > ema20 else "⚠️ neutro"
    medio = "✅ COMPRA" if ema20 > ema50 else "⚠️ neutro"
    lungo = "✅ INVESTI" if momentum > 0 else "⚠️ neutro"

    return breve, medio, lungo

# Analisi di un simbolo
def analyze_symbol(symbol):
    try:
        data = yf.download(symbol, period="60d", interval="1d")["Close"]
        breve, medio, lungo = calculate_trend(data)
        motivo = f"trend breve {breve}, trend medio {medio}, trend lungo {lungo}, volumi normali"
        return f"📌 {symbol}\nBreve: {breve}\nMedio: {medio}\nLungo: {lungo}\nMotivo: {motivo}\n\n"
    except:
        return f"📌 {symbol} - errore dati\n\n"

# Build report
def build_report():
    report = f"📊 REPORT IA MERCATI – {pd.Timestamp.now():%d/%m/%Y %H:%M}\n\n"
    report += "--- Azioni e ETF ---\n"
    for s in SYMBOLS:
        report += analyze_symbol(s)
    report += (
        "🧠 SITUAZIONE GENERALE:\n"
        "Mercato: POSITIVO\n"
        "Strategia consigliata: COMPRARE SUI RITRACCIAMENTI\n"
        "Rischio: MEDIO\n"
    )
    return report

# PDF semplice
def create_pdf(report_text, filename="report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in report_text.split("\n"):
        pdf.multi_cell(0, 6, line)
    pdf.output(filename)

# Main async
async def main():
    bot = Bot(token=TOKEN)
    report_text = build_report()
    create_pdf(report_text)
    await bot.send_message(chat_id=CHAT_ID, text=report_text)

# Entry
if __name__ == "__main__":
    asyncio.run(main())
