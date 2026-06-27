from flask import Flask, request, jsonify
import requests
from datetime import datetime
import random

app = Flask(__name__)

# ===== CONFIGURATION (VOS VRAIES DONNÉES) =====
TELEGRAM_BOT_TOKEN = "8866964539:AAHUOW6TftO2b7aXZ0bA2zLvQwrsumDnayA"
WHATSAPP_SUPPORT_EMAIL = "leseigneur235@gmail.com"  # change ici pour tester avec ton adresse
AUTHORIZED_USERS = ["6815008409"]

MAILJET_API_KEY = "6105b43496004e5005c139b06df09d7a"
MAILJET_API_SECRET = "3756444a0085038f94eb969bec70f5b1"

SENDER_EMAILS = ["azountou@gmail.com"]
# ===== FIN DE LA CONFIGURATION =====

@app.route('/')
def home():
    return "WhatsApp Reporting Service is running!"

@app.route('/debug')
def debug():
    return jsonify({
        "webhook_url": "https://unit-180.vercel.app/telegram-webhook",
        "telegram_token_configured": bool(8866964539:AAHUOW6TftO2b7aXZ0bA2zLvQwrsumDnayA),
        "authorized_users": 6815008409
    })

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    data = request.get_json()
    print(f"Received data: {data}")

    if 'message' in data and 'text' in data['message']:
        chat_id = data['message']['chat']['id']
        user_id = str(data['message']['from']['id'])
        text = data['message']['text']

        if user_id not in AUTHORIZED_USERS:
            send_telegram_message(chat_id, "❌ Vous n'êtes pas autorisé à utiliser ce bot.")
            return jsonify({"status": "unauthorized"})

        if text.startswith('/report'):
            try:
                parts = text.split(' ', 1)
                if len(parts) < 2:
                    send_telegram_message(chat_id, "📌 Usage : /report <texte du signalement>")
                    return jsonify({"status": "error"})

                report_text = parts[1].strip()
                send_whatsapp_report(report_text)
                send_telegram_message(chat_id, "✅ Rapport envoyé avec succès.")
            except Exception as e:
                send_telegram_message(chat_id, f"⚠️ Échec : {str(e)}")

    return jsonify({"status": "success"})

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erreur Telegram: {e}")

def send_whatsapp_report(report_text):
    subject = "Signalement WhatsApp"
    body = f"""Signalement WhatsApp
Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Message :
{report_text}
"""

    try:
        from mailjet_rest import Client
        sender_email = random.choice(SENDER_EMAILS)
        mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3.1')
        data = {
            'Messages': [{
                "From": {"Email": sender_email, "Name": "WhatsApp Reporter"},
                "To": [{"Email": WHATSAPP_SUPPORT_EMAIL, "Name": "WhatsApp Support"}],
                "Subject": subject,
                "TextPart": body
            }]
        }
        result = mailjet.send.create(data=data)
        if result.status_code != 200:
            error_detail = result.json() if result.text else "Aucun détail"
            raise Exception(f"Mailjet error {result.status_code}: {error_detail}")
    except Exception as e:
        raise Exception(f"Erreur Mailjet: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
