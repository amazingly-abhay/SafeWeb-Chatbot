from flask import Flask, request, jsonify
import requests, os, json
from datetime import datetime

app = Flask(__name__)

# Load env vars safely
TOKEN = os.getenv('TOKEN')
PHONE_ID = os.getenv('PHONE_ID')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_SAFE_API_KEY')

# Track user states
user_states = {}

# =====================================================
# Helper: Send message via WhatsApp Cloud API
# =====================================================
def send_whatsapp_message(data):
    url = f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    r = requests.post(url, json=data, headers=headers)
    print("SEND RESPONSE:", r.status_code, r.text)
    return r.status_code


def send_message(to, text):
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    return send_whatsapp_message(data)


def send_menu(to):
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "🚨 *SafeWeb Bot* 🚨\n\nHello! How can we help you today?"
            },
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "1", "title": "🔍 Check Phishing URL"}},
                    {"type": "reply", "reply": {"id": "2", "title": "🚨 File Harassment Complaint"}},
                    {"type": "reply", "reply": {"id": "3", "title": "🛡️ Safety Tips"}}
                ]
            }
        }
    }
    return send_whatsapp_message(data)

# =====================================================
# Google Safe Browsing API for phishing URL check
# =====================================================
def check_phishing(url):
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "YOUR_KEY_HERE":
        return "⚠️ Safe Browsing API not configured"

    lookup_url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={GOOGLE_API_KEY}"
    payload = {
        "client": {"clientId": "safeweb", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }
    r = requests.post(lookup_url, json=payload)
    result = r.json()

    if result == {}:
        return f"✅ *SAFE* ✅\n\n{url}\nNo threats found!"
    else:
        return f"🚨 *DANGEROUS SITE DETECTED* 🚨\n\n{url}\n⚠️ Phishing / Malware risk!\nDo NOT click or enter details!"

# =====================================================
# Webhook verification (GET)
# =====================================================
@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print("Webhook Verified!")
        return challenge, 200
    return "Forbidden", 403

# =====================================================
# Webhook handler (POST)
# =====================================================

@app.route('/webhook', methods=['POST'])
def webhook():
    body = request.get_json()
    print(json.dumps(body, indent=2))
    try:
        phone = body['entry'][0]['changes'][0]['value']['messages'][0]['from']
        send_message(phone, "Bot is alive 🚀")
    except Exception as e:
        print("Error:", e)
    return "OK", 200

# @app.route('/webhook', methods=['POST'])
# def webhook():
#     body = request.get_json()
#     print("WEBHOOK BODY:", json.dumps(body, indent=2))

#     if body.get('object'):
#         for entry in body.get('entry', []):
#             for change in entry.get('changes', []):
#                 value = change.get('value', {})
#                 messages = value.get('messages', [])

#                 for msg in messages:
#                     phone = msg.get('from')
#                     msg_type = msg.get('type')

#                     # --- Handle text messages or button replies ---
#                     if msg_type == "text":
#                         msg_body = msg["text"]["body"].lower()
#                     elif msg_type == "interactive":
#                         msg_body = msg["interactive"]["button_reply"]["id"]
#                     else:
#                         msg_body = ""

#                     print(f"User ({phone}) said: {msg_body}")

#                     # --- Handle message logic ---
#                     if 'hello' in msg_body:
#                         send_menu(phone)

#                     elif msg_body == "1":
#                         send_message(phone, "Send me the suspicious URL 🔗\nExample: https://fake-bank.com")
#                         user_states[phone] = "waiting_url"

#                     elif msg_body == "2":
#                         send_message(phone, "Describe the harassment incident (who, what platform, screenshots if any). We'll file it anonymously.")
#                         user_states[phone] = "waiting_complaint"

#                     elif msg_body == "3":
#                         send_message(phone, "🛡️ Safety Tips:\n1️⃣ Avoid clicking unknown links.\n2️⃣ Enable 2FA.\n3️⃣ Don’t share OTPs.\n4️⃣ Report suspicious accounts.")
#                         send_menu(phone)

#                     elif user_states.get(phone) == "waiting_url" and msg_body.startswith("http"):
#                         result = check_phishing(msg_body)
#                         send_message(phone, result)
#                         del user_states[phone]
#                         send_menu(phone)

#                     elif user_states.get(phone) == "waiting_complaint":
#                         send_message(phone, f"✅ Complaint received!\nReference ID: SC2025-{phone[-4:]}\nWe'll take action within 24 hrs.")
#                         del user_states[phone]
#                         send_menu(phone)

#                     else:
#                         send_menu(phone)

#     return "OK", 200


# =====================================================
# Run Flask
# =====================================================
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8000)))
