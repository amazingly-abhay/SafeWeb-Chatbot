from flask import Flask, request
import requests, os, json

app = Flask(__name__)

# Load credentials from environment variables (set these in Render / local .env)
TOKEN = os.getenv('TOKEN')
PHONE_ID = os.getenv('PHONE_ID')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')

# --- Helper to send WhatsApp messages ---
def send_message(to, text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    r = requests.post(url, json=payload, headers=headers)
    print("SEND RESPONSE:", r.status_code, r.text)
    return r.status_code

# --- Webhook verification ---
@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verified!")
        return challenge, 200
    else:
        return "Forbidden", 403

# --- Main webhook logic ---
@app.route('/webhook', methods=['POST'])
def webhook():
    body = request.get_json()
    print("WEBHOOK BODY:", json.dumps(body, indent=2))

    try:
        msg = body['entry'][0]['changes'][0]['value']['messages'][0]
        phone = msg['from']
        text = msg.get('text', {}).get('body', '')
        print(f"Received from {phone}: {text}")

        # Simple auto-reply
        send_message(phone, "Hello from SafeWeb Bot 👋"+text)

    except Exception as e:
        print("Error processing message:", e)

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
