from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# ===== CONFIGURATION À MODIFIER =====
# Remplacez ces valeurs par vos informations réelles
TELEGRAM_BOT_TOKEN = "VOTRE_TOKEN_BOT_TELEGRAM_ICI"
WHATSAPP_SUPPORT_EMAIL = "support@whatsapp.com"  # Adresse e-mail du support WhatsApp
AUTHORIZED_USERS = ["ID_UTILISATEUR_1", "ID_UTILISATEUR_2"]  # IDs Telegram autorisés (séparés par des virgules)
SENDER_EMAIL = "votre_email@exemple.com"  # Votre e-mail d'envoi
SENDGRID_API_KEY = "VOTRE_CLE_API_SENDGRID_ICI"  # Clé API SendGrid
# ===== FIN DE LA CONFIGURATION =====

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
    
    # Configuration du service d'envoi d'e-mails avec SendGrid
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=WHATSAPP_SUPPORT_EMAIL,
            subject=subject,
            html_content=body
        )
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code == 202
        
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail: {str(e)}")
        return False

if __name__ == '__main__':
    app.run(debug=True)
