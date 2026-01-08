from telegram import Bot
from datetime import datetime

# Inserisci qui il tuo token e chat ID già presenti nei Secrets
TELEGRAM_TOKEN = "<IL TUO TOKEN>"
CHAT_ID = "<IL TUO CHAT_ID>"

# Messaggio di esempio fisso (puoi aggiornarlo dinamicamente più avanti)
def get_daily_report():
    today = datetime.now().strftime("%d/%m/%Y %H:%M")
    report = f"""📊 REPORT IA MERCATI – {today}

--- Azioni USA ---
📌 AAPL
Breve: ⚠️ neutro
Medio: ✅ COMPRA
Lungo: ✅ INVESTI
Motivo: trend breve ⚠️ neutro, trend medio ✅ COMPRA, trend lungo ✅ INVESTI, volumi normali

📌 GOOGL
Breve: ⚠️ neutro
Medio: ✅ COMPRA
Lungo: ✅ INVESTI
Motivo: trend breve ⚠️ neutro, trend medio ✅ COMPRA, trend lungo ✅ INVESTI, volumi normali

📌 META
Breve: ✅ COMPRA
Medio: ✅ COMPRA
Lungo: ✅ INVESTI
Motivo: trend breve ✅ COMPRA, trend medio ✅ COMPRA, trend lungo ✅ INVESTI, volumi normali

🧠 SITUAZIONE GENERALE:
Mercato: POSITIVO
Strategia consigliata: COMPRARE SUI RITRACCIAMENTI
Rischio: MEDIO
"""
    return report

def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    message = get_daily_report()
    bot.send_message(chat_id=CHAT_ID, text=message)
    print("✅ Messaggio inviato!")

if __name__ == "__main__":
    main()
