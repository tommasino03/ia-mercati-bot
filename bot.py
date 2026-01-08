from telegram import Bot
from datetime import datetime

# Inserisci qui il tuo token e chat ID dai Secrets
TELEGRAM_TOKEN = "<IL TUO TOKEN>"
CHAT_ID = "<IL TUO CHAT_ID>"

# Liste dei titoli da includere nel report
azioni_usa = [
    "AAPL", "GOOGL", "META", "TSLA", "JPM", "BAC",
    "V", "MA", "ADBE", "CSCO", "CMCSA", "PEP", "KO", "WMT"
]

etf = [
    "SPY", "QQQ", "VEA", "VGK", "IWV", "VTI", "EFA", "IEMG"
]

azioni_europa = ["SAN.MC"]

# Trend fissi per ora (puoi cambiare poi con logica dinamica)
def trend_breve(ticker): return "✅ COMPRA" if ticker != "AAPL" else "⚠️ neutro"
def trend_medio(ticker): return "✅ COMPRA"
def trend_lungo(ticker): return "✅ INVESTI"

def get_daily_report():
    today = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"📊 REPORT IA MERCATI – {today}\n\n"

    report += "--- Azioni USA ---\n"
    for ticker in azioni_usa:
        report += (
            f"📌 {ticker}\n"
            f"Breve: {trend_breve(ticker)}\n"
            f"Medio: {trend_medio(ticker)}\n"
            f"Lungo: {trend_lungo(ticker)}\n"
            f"Motivo: trend breve {trend_breve(ticker)}, "
            f"trend medio {trend_medio(ticker)}, "
            f"trend lungo {trend_lungo(ticker)}, volumi normali\n\n"
        )

    report += "--- ETF ---\n"
    for ticker in etf:
        report += (
            f"📌 {ticker}\n"
            f"Breve: {trend_breve(ticker)}\n"
            f"Medio: {trend_medio(ticker)}\n"
            f"Lungo: {trend_lungo(ticker)}\n"
            f"Motivo: trend breve {trend_breve(ticker)}, "
            f"trend medio {trend_medio(ticker)}, "
            f"trend lungo {trend_lungo(ticker)}, volumi normali\n\n"
        )

    report += "--- Azioni Europa ---\n"
    for ticker in azioni_europa:
        report += (
            f"📌 {ticker}\n"
            f"Breve: {trend_breve(ticker)}\n"
            f"Medio: {trend_medio(ticker)}\n"
            f"Lungo: {trend_lungo(ticker)}\n"
            f"Motivo: trend breve {trend_breve(ticker)}, "
            f"trend medio {trend_medio(ticker)}, "
            f"trend lungo {trend_lungo(ticker)}, volumi normali\n\n"
        )

    report += "🧠 SITUAZIONE GENERALE:\n"
    report += "Mercato: POSITIVO\n"
    report += "Strategia consigliata: COMPRARE SUI RITRACCIAMENTI\n"
    report += "Rischio: MEDIO\n"

    return report

def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    message = get_daily_report()
    bot.send_message(chat_id=CHAT_ID, text=message)
    print("✅ Messaggio inviato!")

if __name__ == "__main__":
    main()
