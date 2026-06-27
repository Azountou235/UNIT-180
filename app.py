from flask import Flask, request, jsonify
import requests
from datetime import datetime
import random

app = Flask(__name__)

# ===== CONFIGURATION (VOS VRAIES DONNÉES) =====
TELEGRAM_BOT_TOKEN = "8866964539:AAHUOW6TftO2b7aXZ0bA2zLvQwrsumDnayA"
WHATSAPP_SUPPORT_EMAIL = "leseigneur235@gmail.com"  # ← Changé pour ton adresse de test
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
        "telegram_token_configured": bool(TELEGRAM_BOT_TOKEN),
        "authorized_users": AUTHORIZED_USERS,
        "destination_email": WHATSAPP_SUPPORT_EMAIL,
        "sender_email": SENDER_EMAILS[0]
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
                    send_telegram_message(chat_id, "📌 Usage : /report <texte du signalement>\nEx: /report Ce numéro m'envoie des menaces")
                    return jsonify({"status": "error"})

                report_text = parts[1].strip()
                result_msg = send_whatsapp_report(report_text)
                send_telegram_message(chat_id, result_msg)
            except Exception as e:
                send_telegram_message(chat_id, f"⚠️ Erreur: {str(e)}")

    return jsonify({"status": "success"})

def send_whatsapp_report(report_text):
    subject = f"Signalement WhatsApp - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    body = f"""NOUVEAU SIGNALEMENT WHATSAPP
==============================
Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

MESSAGE REÇU :
{report_text}
==============================
"""

    try:
        from mailjet_rest import Client
        
        print(f"🔍 Tentative d'envoi via Mailjet...")
        print(f"📧 Expéditeur : {SENDER_EMAILS[0]}")
        print(f"📥 Destinataire : {WHATSAPP_SUPPORT_EMAIL}")
        print(f"🔑 API Key : {MAILJET_API_KEY[:10]}...")
        
        sender_email = random.choice(SENDER_EMAILS)
        mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3.1')
        
        data = {
            'Messages': [{
                "From": {"Email": sender_email, "Name": "WhatsApp Reporter"},
                "To": [{"Email": WHATSAPP_SUPPORT_EMAIL, "Name": "Support"}],
                "Subject": subject,
                "TextPart": body
            }]
        }
        
        print(f"📤 Envoi de la requête...")
        result = mailjet.send.create(data=data)
        print(f"📊 Status code: {result.status_code}")
        print(f"📋 Réponse complète: {result.json()}")
        
        if result.status_code == 200:
            # Vérifier si l'email a vraiment été accepté
            response_data = result.json()
            messages = response_data.get('Messages', [])
            if messages:
                for msg in messages:
                    if msg.get('Status') == 'success':
                        return f"✅ Rapport bien envoyé à {WHATSAPP_SUPPORT_EMAIL}\n📧 Vérifiez vos spams"
                    else:
                        error = msg.get('Errors', [])
                        return f"❌ Erreur Mailjet: {error}"
            return f"✅ Rapport envoyé (statut 200) à {WHATSAPP_SUPPORT_EMAIL}"
        else:
            error_detail = result.json() if result.text else "Aucun détail"
            return f"❌ Échec Mailjet ({result.status_code}): {error_detail}"
            
    except Exception as e:
        print(f"💥 Exception: {str(e)}")
        return f"❌ Erreur technique: {str(e)}"

# Ne pas inclure app.run() pour Vercel
