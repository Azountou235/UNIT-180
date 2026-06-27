from flask import Flask, request, jsonify
import requests
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import threading

app = Flask(__name__)

# ===== CONFIGURATION =====
TELEGRAM_BOT_TOKEN = "8866964539:AAHUOW6TftO2b7aXZ0bA2zLvQwrsumDnayA"
AUTHORIZED_USERS = ["6815008409"]
ADMIN_WHATSAPP = "+235 91234567"

# Liste des emails destinataires
DESTINATION_EMAILS = [
    "support@support.whatsapp.com",
    "android_web@support.whatsapp.com",
    "iphone_web@support.whatsapp.com",
    "smb_web@support.whatsapp.com",
    "businesscomplaints@support.whatsapp.com",
    "accessibility@support.whatsapp.com"
]

# Comptes Gmail (expéditeurs)
GMAIL_ACCOUNTS = [
    {"email": "azountouleseigneur@gmail.com", "password": "oeddtrnjoxlnubej"}
]

NOMBRE_ENVOIS = 20  # Nombre d'envois par destinataire
INTERVALLE_SECONDES = 15  # Intervalle entre chaque cycle d'envoi
# ===== FIN CONFIGURATION =====

# Stockage des tentatives non autorisées
unauthorized_attempts = {}
# Variable pour bloquer les nouvelles commandes pendant l'envoi
is_sending = False

@app.route('/')
def home():
    return "WhatsApp Reporting Service is running!"

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    global is_sending, unauthorized_attempts
    
    data = request.get_json()
    
    if 'message' in data and 'text' in data['message']:
        chat_id = data['message']['chat']['id']
        user_id = str(data['message']['from']['id'])
        text = data['message']['text']

        # Vérifier si l'utilisateur est autorisé
        if user_id not in AUTHORIZED_USERS:
            handle_unauthorized(chat_id, user_id)
            return jsonify({"status": "unauthorized"})

        if text.startswith('/report'):
            # Vérifier si un envoi est déjà en cours
            if is_sending:
                send_telegram_message(chat_id, "⏳ Veuillez patienter, des e-mails sont en cours d'envoi...")
                return jsonify({"status": "busy"})
            
            parts = text.split(' ', 1)
            if len(parts) < 2:
                send_telegram_message(chat_id, "📌 Usage : /report <texte du signalement>")
                return jsonify({"status": "error"})

            report_text = parts[1].strip()
            
            # Lancer l'envoi dans un thread séparé
            thread = threading.Thread(target=send_multiple_reports, args=(chat_id, report_text))
            thread.start()
            
            total_emails = NOMBRE_ENVOIS * len(DESTINATION_EMAILS)
            send_telegram_message(chat_id, f"🚀 Début d'envoi de {NOMBRE_ENVOIS} emails vers chacun des {len(DESTINATION_EMAILS)} destinataires ({total_emails} emails au total)...")

    return jsonify({"status": "success"})

def handle_unauthorized(chat_id, user_id):
    global unauthorized_attempts
    
    if user_id not in unauthorized_attempts:
        unauthorized_attempts[user_id] = 0
    
    unauthorized_attempts[user_id] += 1
    attempts = unauthorized_attempts[user_id]
    
    if attempts == 1:
        message = """┏━━━━━━━━━━━━━━━━━━━━┓
   🔒  *ACCÈS REFUSÉ* 🔒
┗━━━━━━━━━━━━━━━━━━━━┛

Cher frère, vous n'êtes pas autorisé à utiliser ce bot. 

Pour obtenir l'accès, merci de contacter l'Administrateur sur WhatsApp : 👉 *""" + ADMIN_WHATSAPP + """*

🗣️ _LE SEIGNEUR DES APPAREILS 🇷🇴_"""
    
    elif attempts == 2:
        message = """┏━━━━━━━━━━━━━━━━━━━━┓
   🚫  *AVERTISSEMENT*  🚫
┗━━━━━━━━━━━━━━━━━━━━┛

N'est-ce pas la deuxième fois que tu recommences alors que je t'ai dit accès refusé ? 

🛑 *Ne fais pas ça !*
💬 *Vas-y WhatsApp :* """ + ADMIN_WHATSAPP + """

🗣️ _LE SEIGNEUR DES APPAREILS 🇷🇴_"""
    
    elif attempts == 3:
        message = """🚨 *[ BANNI DÉFINITIF ]* 🚨

C'est fini, vous êtes banni complètement. 

❌ *Accès définitivement révoqué.*
🗣️ _LE SEIGNEUR 🇷🇴_"""
    
    elif attempts == 4:
        message = "🖕🏿"
    
    else:
        return
    
    send_telegram_message(chat_id, message)

def send_multiple_reports(chat_id, report_text):
    global is_sending
    is_sending = True
    total_emails = NOMBRE_ENVOIS * len(DESTINATION_EMAILS)
    
    try:
        for cycle in range(1, NOMBRE_ENVOIS + 1):
            destinataires_str = ""
            
            for dest_email in DESTINATION_EMAILS:
                try:
                    gmail_account = GMAIL_ACCOUNTS[cycle % len(GMAIL_ACCOUNTS)]
                    
                    send_email_gmail(
                        gmail_account["email"],
                        gmail_account["password"],
                        dest_email,
                        report_text
                    )
                    destinataires_str += f"✅ {dest_email}\n"
                except Exception as e:
                    destinataires_str += f"❌ {dest_email}: {str(e)}\n"
            
            emails_envoyes = cycle * len(DESTINATION_EMAILS)
            confirmation = f"""📤 *Cycle {cycle}/{NOMBRE_ENVOIS}* ({emails_envoyes}/{total_emails} emails)

📧 Destinataires :
{destinataires_str}
⏱️ Prochain cycle dans {INTERVALLE_SECONDES}s..."""
            
            send_telegram_message(chat_id, confirmation)
            
            if cycle < NOMBRE_ENVOIS:
                time.sleep(INTERVALLE_SECONDES)
        
        send_telegram_message(chat_id, f"✅ *TERMINÉ !*\n{total_emails} emails envoyés avec succès vers {len(DESTINATION_EMAILS)} destinataires.")
        
    except Exception as e:
        send_telegram_message(chat_id, f"❌ Erreur: {str(e)}")
    
    finally:
        is_sending = False

def send_email_gmail(gmail_user, gmail_password, to_email, report_text):
    subject = "Demande de l'aide"
    body = report_text

    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(gmail_user, gmail_password)
    server.send_message(msg)
    server.quit()

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        pass
