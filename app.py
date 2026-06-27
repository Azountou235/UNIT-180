from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

# Configuration depuis les variables d'environnement
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WHATSAPP_SUPPORT_EMAIL = os.environ.get("WHATSAPP_SUPPORT_EMAIL")
AUTHORIZED_USERS = os.environ.get("AUTHORIZED_USERS", "").split(",")

@app.route('/')
def home():
    return "WhatsApp Reporting Service is running!"

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    data = request.get_json()
    
    # Vérifier si c'est une commande /report
    if 'message' in data and 'text' in data['message']:
        chat_id = data['message']['chat']['id']
        user_id = str(data['message']['from']['id'])
        text = data['message']['text']
        
        # Vérifier si l'utilisateur est autorisé
        if user_id not in AUTHORIZED_USERS:
            send_telegram_message(chat_id, "Vous n'êtes pas autorisé à utiliser ce bot.")
            return jsonify({"status": "unauthorized"})
        
        # Traiter la commande /report
        if text.startswith('/report'):
            try:
                # Extraire le numéro de téléphone
                phone_number = text.split('/report ')[1].strip()
                
                # Envoyer le rapport à WhatsApp
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
    # Préparer le contenu de l'e-mail
    subject = f"Signalement d'utilisateur abusif - {phone_number}"
    body = f"""
    Signalement d'utilisateur WhatsApp abusif:
    
    Numéro: {phone_number}
    Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Cet utilisateur a été signalé pour comportement inapproprié.
    Veuillez prendre les mesures nécessaires.
    """
    
    # Configuration du service d'envoi d'e-mails (vous devrez utiliser un service comme SendGrid, Mailgun, etc.)
    # C'est un exemple avec SendGrid
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        message = Mail(
            from_email=os.environ.get("SENDER_EMAIL"),
            to_emails=WHATSAPP_SUPPORT_EMAIL,
            subject=subject,
            html_content=body
        )
        
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.send(message)
        return response.status_code == 202
        
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail: {str(e)}")
        return False

if __name__ == '__main__':
    app.run(debug=True)
