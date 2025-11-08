from flask import Flask, request
import requests, os
from datetime import datetime

app = Flask(__name__)

TOKEN    = os.environ['TOKEN']
PHONE_ID = os.environ['PHONE_ID']
VERIFY   = "renderbot"

def send(to, text):
    requests.post(
        f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    )

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY:
            return request.args.get("hub.challenge")
        return "Invalid token", 403

    data = request.get_json()
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            msg = change["value"].get("messages", [{}])[0]
            if not msg: continue
            sender = msg["from"]
            text = msg["text"]["body"].lower().strip()

            if "hi" in text:
                reply = "Render Bot is LIVE!\nNo ngrok, no Replit.\nType *menu*"
            elif "time" in text:
                reply = f"Time: {datetime.now():%H:%M:%S}"
            elif "menu" in text:
                reply = "hi | time | ai [question]"
            elif text.startswith("ai "):
                reply = f"You asked AI: {text[3:]}"
            else:
                reply = f"Echo: {text}"

            send(sender, reply)
    return "OK", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8000)))