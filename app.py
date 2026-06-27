from flask import Flask, request, jsonify
import requests
from datetime import datetime
import random

app = Flask(__name__)

# ===== CONFIGURATION À MODIFIER =====
TELEGRAM_BOT_TOKEN = "8866964539:AAHUOW6TftO2b7aXZ0bA2zLvQwrsumDnayA"
WHATSAPP_SUPPORT_EMAIL = "support@support.whatsapp.com"
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

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    data = request.get_json()
    
    if 'message' in data and 'text' in data['message']:
        chat_id = data['message']['chat']['id']
        user_id = str(data['message']['from']['id'])
        text = data['message']['text']
        
        if user_id not in AUTHORIZED_USERS:
            send_telegram_message(chat_id, "Vous n'êtes pas autorisé à utiliser ce bot.")
            return jsonify({"status": "unauthorized"})
        
        if text.startswith('/report'):
            try:
                phone_number = text.split('/report ')[1].strip()
                report_status = send_whatsapp_report(phone_number)
                
                if report_status:
                    send_telegram_message(chat_id, f"Rapport envoyé avec succès pour le numéro {phone_number}")
                else:
                    send_telegram_message(chat_id, "Échec de l'envoi du rapport. Veuillez réessayer.")
                    
            except Exception as e:
                send_telegram_message(chat_id, f"Erreur: {str(e)}")
    
    return jsonify({"status": "success"})

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(url, json=payload)
    return response.status_code == 200

def send_whatsapp_report(phone_number):
    subject = f"Signalement d'utilisateur abusif - {phone_number}"
    body = f"""
    Signalement d'utilisateur WhatsApp abusif:
    
    Numéro: {phone_number}
    Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Cet utilisateur a été signalé pour comportement inapproprié.
    Veuillez prendre les mesures nécessaires.
    """
    
    try:
        import mailjet_rest
        
        # Choisir une adresse d'envoi au hasard
        sender_email = random.choice(SENDER_EMAILS)
        
        mailjet = mailjet_rest.Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3.1')
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
