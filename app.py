from flask import Flask, request, jsonify
import requests
from datetime import datetime
import random

app = Flask(__name__)

# ===== CONFIGURATION (VOS VRAIES DONNÉES) =====
TELEGRAM_BOT_TOKEN = "8866964539:AAHUOW6TftO2b7aXZ0bA2zLvQwrsumDnayA"
WHATSAPP_SUPPORT_EMAIL = "leseigneur235@gmail.com"
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
        "status": "ok",
        "webhook_url": "https://unit-180.vercel.app/telegram-webhook",
        "token_ok": bool(TELEGRAM_BOT_TOKEN),
        "mailjet_key_ok": bool(MAILJET_API_KEY),
        "users": AUTHORIZED_USERS
    })

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    try:
        data = request.get_json()
        
        if 'message' not in data:
            return jsonify({"status": "no_message"})
            
        if 'text' not in data['message']:
            return jsonify({"status": "no_text"})
        
        chat_id = data['message']['chat']['id']
        user_id = str(data['message']['from']['id'])
        text = data['message']['text']

        if user_id not in AUTHORIZED_USERS:
            send_telegram_message(chat_id, "❌ Vous n'êtes pas autorisé à utiliser ce bot.")
            return jsonify({"status": "unauthorized"})

        if text.startswith('/report'):
            parts = text.split(' ', 1)
            if len(parts) < 2:
                send_telegram_message(chat_id, "📌 Usage : /report <texte>\nEx: /report Ce compte spamme")
                return jsonify({"status": "no_text"})

            report_text = parts[1].strip()
            
            # Envoi email
            success, message = send_whatsapp_report(report_text)
            send_telegram_message(chat_id, message)
            
            return jsonify({"status": "success", "email_sent": success})
        
        return jsonify({"status": "command_not_recognized"})
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

def send_telegram_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Erreur Telegram: {e}")
        return False

def send_whatsapp_report(report_text):
    try:
        from mailjet_rest import Client
        
        sender_email = SENDER_EMAILS[0]
        
        mailjet = Client(
            auth=(MAILJET_API_KEY, MAILJET_API_SECRET),
            version='v3.1'
        )
        
        data = {
            'Messages': [{
                "From": {
                    "Email": sender_email,
                    "Name": "WhatsApp Reporter"
                },
                "To": [{
                    "Email": WHATSAPP_SUPPORT_EMAIL,
                    "Name": "Support"
                }],
                "Subject": f"Signalement - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                "TextPart": f"""Signalement WhatsApp
Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Message :
{report_text}
"""
            }]
        }
        
        result = mailjet.send.create(data=data)
        
        if result.status_code == 200:
            return True, f"✅ Rapport envoyé à {WHATSAPP_SUPPORT_EMAIL}"
        else:
            error = result.json()
            return False, f"❌ Erreur Mailjet: {error}"
            
    except Exception as e:
        return False, f"❌ Erreur: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
