from flask import Flask, request, jsonify
import requests
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# ===== CONFIGURATION =====
TELEGRAM_BOT_TOKEN = "8866964539:AAHUOW6TftO2b7aXZ0bA2zLvQwrsumDnayA"
WHATSAPP_SUPPORT_EMAIL = "leseigneur235@gmail.com"
AUTHORIZED_USERS = ["6815008409"]

# Gmail
GMAIL_USER = "azountouleseigneur@gmail.com"
GMAIL_PASSWORD = "oeddtrnjoxlnubej"  # ← Sans les espaces
# ===== FIN CONFIGURATION =====

@app.route('/')
def home():
    return "WhatsApp Reporting Service is running!"

@app.route('/debug')
def debug():
    return jsonify({
        "webhook_url": "https://unit-180.vercel.app/telegram-webhook",
        "telegram_token_configured": bool(TELEGRAM_BOT_TOKEN),
        "authorized_users": AUTHORIZED_USERS,
        "gmail_configured": bool(GMAIL_PASSWORD != "METTRE_LE_MOT_DE_PASSE_16_CARACTERES_ICI")
    })

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    data = request.get_json()
    
    if 'message' in data and 'text' in data['message']:
        chat_id = data['message']['chat']['id']
        user_id = str(data['message']['from']['id'])
        text = data['message']['text']

        if user_id not in AUTHORIZED_USERS:
            send_telegram_message(chat_id, "❌ Vous n'êtes pas autorisé à utiliser ce bot.")
            return jsonify({"status": "unauthorized"})

        if text.startswith('/report'):
            parts = text.split(' ', 1)
            if len(parts) < 2:
                send_telegram_message(chat_id, "📌 Usage : /report <texte du signalement>\nEx: /report Ce numéro m'envoie des menaces")
                return jsonify({"status": "error"})

            report_text = parts[1].strip()
            
            try:
                send_email_gmail(report_text)
                send_telegram_message(chat_id, f"✅ Signalement envoyé avec succès à {WHATSAPP_SUPPORT_EMAIL}")
            except Exception as e:
                send_telegram_message(chat_id, f"❌ Erreur: {str(e)}")

    return jsonify({"status": "success"})

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload)
    except:
        pass

def send_email_gmail(report_text):
    subject = f"Signalement WhatsApp - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    body = f"""NOUVEAU SIGNALEMENT WHATSAPP
==============================
Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

MESSAGE :
{report_text}
==============================
"""

    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = WHATSAPP_SUPPORT_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(GMAIL_USER, GMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()
