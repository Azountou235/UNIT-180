from flask import Flask, request, jsonify
import requests
from datetime import datetime
import random

app = Flask(__name__)

# ===== CONFIGURATION (VOS VRAIES DONNÉES) =====
TELEGRAM_BOT_TOKEN = "8866964539:AAHUOW6TftO2b7aXZ0bA2zLvQwrsumDnayA"
WHATSAPP_SUPPORT_EMAIL = "azountouleseigneur@gmail.com"
AUTHORIZED_USERS = ["6815008409"]

# Configuration Mailjet
MAILJET_API_KEY = "6105b43496004e5005c139b06df09d7a"
MAILJET_API_SECRET = "3756444a0085038f94eb969bec70f5b1"

# Adresses e-mail d'envoi (doivent être vérifiées dans votre compte Mailjet)
SENDER_EMAILS = [
    "azountou@gmail.com"
]
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
    print(f"Received data: {data}")  # Pour le débogage

    if 'message' in data and 'text' in data['message']:
        chat_id = data['message']['chat']['id']
        user_id = str(data['message']['from']['id'])
        text = data['message']['text']

        if user_id not in AUTHORIZED_USERS:
            send_telegram_message(chat_id, "❌ Vous n'êtes pas autorisé à utiliser ce bot.")
            return jsonify({"status": "unauthorized"})

        if text.startswith('/report'):
            try:
                # Sépare la commande "/report" du reste
                parts = text.split(' ', 1)
                if len(parts) < 2:
                    send_telegram_message(chat_id, "📌 Usage : /report <numéro> [message]\nEx: /report +235 90 12 34 56 menace")
                    return jsonify({"status": "error"})

                rest = parts[1].strip()
                # Récupère le numéro (premier mot) et le message éventuel (le reste)
                args = rest.split(' ', 1)
                phone_number = args[0]
                custom_message = args[1] if len(args) > 1 else ""

                report_status = send_whatsapp_report(phone_number, custom_message)

                if report_status:
                    send_telegram_message(chat_id, f"✅ Rapport envoyé avec succès pour {phone_number}")
                else:
                    send_telegram_message(chat_id, "❌ Échec de l'envoi du rapport. Veuillez réessayer.")

            except Exception as e:
                send_telegram_message(chat_id, f"⚠️ Erreur: {str(e)}")

    return jsonify({"status": "success"})

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Erreur Telegram: {e}")
        return False

def send_whatsapp_report(phone_number, custom_message=""):
    # Sujet de l'email
    subject = f"Signalement d'utilisateur abusif - {phone_number}"

    # Corps de l'email avec ou sans message personnalisé
    if custom_message:
        body = f"""Signalement WhatsApp
Numéro : {phone_number}
Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Message de l'utilisateur :
{custom_message}
"""
    else:
        body = f"""Signalement WhatsApp
Numéro : {phone_number}
Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Cet utilisateur a été signalé pour comportement inapproprié.
Veuillez prendre les mesures nécessaires.
"""

    try:
        # Import ici pour ne pas dépendre du module s'il n'est pas utilisé
        from mailjet_rest import Client

        sender_email = random.choice(SENDER_EMAILS)
        mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3.1')

        data = {
            'Messages': [
                {
                    "From": {
                        "Email": sender_email,
                        "Name": "WhatsApp Reporter"
                    },
                    "To": [
                        {
                            "Email": WHATSAPP_SUPPORT_EMAIL,
                            "Name": "WhatsApp Support"
                        }
                    ],
                    "Subject": subject,
                    "TextPart": body
                }
            ]
        }
        result = mailjet.send.create(data=data)
        return result.status_code == 200
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail: {str(e)}")
        return False

if __name__ == '__main__':
    app.run(debug=True)
