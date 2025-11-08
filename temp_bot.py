from flask import Flask, request, jsonify
import requests, os,json
from datetime import datetime

app = Flask(__name__)

TOKEN      = os.environ['TOKEN']
PHONE_ID   = os.environ['PHONE_ID']
VERIFY_TOKEN  = os.environ['VERIFY_TOKEN']   # ← NOW FROM RENDER

def send(to, text):
    requests.post(
        f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    )

@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print("Webhook Verified!")
        return challenge, 200
    return "Forbidden", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    body = request.get_json()
    
    if body.get('object'):
        for entry in body.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})
                if 'messages' in value:
                    for msg in value['messages']:
                        phone = msg['from']
                        msg_body = msg.get('text', {}).get('body', '').lower()
                        
                        # START WITH "hello"
                        if 'hello' in msg_body:
                            send_menu(phone)
                        elif msg_body == "1":
                            send_message(phone, "Send me the suspicious URL 🔗\nExample: https://fake-bank.com")
                            # Store state (simple way)
                            user_states[phone] = "waiting_url"
                        elif msg_body == "2":
                            send_message(phone, "Describe the harassment incident (who, what platform, screenshots if any). We'll file it anonymously.")
                            user_states[phone] = "waiting_complaint"
                        elif user_states.get(phone) == "waiting_url" and msg_body.startswith("http"):
                            result = check_phishing(msg_body)
                            send_message(phone, result)
                            del user_states[phone]
                            send_menu(phone)  # back to menu
                        elif user_states.get(phone) == "waiting_complaint":
                            # File complaint (here we just forward to email or DB)
                            send_message(phone, "✅ Complaint received! Reference ID: SC2025-" + phone[-4:] + "\nWe'll take action within 24hrs.")
                            # TODO: Save to Google Sheet / Email
                            del user_states[phone]
                            send_menu(phone)
                        else:
                            send_menu(phone)
    return "OK", 200

user_states = {}

def send_menu(phone):
    message = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "🚨 *SafeWeb Bot* 🚨\n\nHello! How can we help you today?"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "1", "title": "🔍 Check Phishing URL"}},
                    {"type": "reply", "reply": {"id": "2", "title": "🚨 File Harassment Complaint"}},
                    {"type": "reply", "reply": {"id": "3", "title": "🛡️ Safety Tips"}}
                ]
            }
        }
    }
    send_whatsapp_message(message)
    
def check_phishing(url):
    api_key = os.environ.get("GOOGLE_SAFE_API_KEY", "YOUR_KEY_HERE")  # Get free key from Google
    if not api_key or api_key == "YOUR_KEY_HERE":
        return "⚠️ Safe Browsing API not configured"
    
    lookup_url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}"
    payload = {
        "client": {"clientId": "safeweb", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "THREAT_TYPE_UNSPECIFIED"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }
    r = requests.post(lookup_url, json=payload)
    if r.json() == {}:
        return f"✅ *SAFE* ✅\n\n{url}\nNo threats found!"
    else:
        return f"🚨 *DANGEROUS SITE DETECTED* 🚨\n\n{url}\n⚠️ Phishing / Malware risk!\nDo NOT click or enter details!"

def send_whatsapp_message(data):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages"
    requests.post(url, json=data, headers=headers)

def send_message(to, text):
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    send_whatsapp_message(data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8000)))
