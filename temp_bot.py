from flask import Flask, request
import requests, os
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

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY:
            return request.args.get("hub.challenge")
        return "Wrong token", 403

    # —— MESSAGE RECEIVED ——
    for entry in request.json.get("entry", []):
        for change in entry.get("changes", []):
            msg = change["value"].get("messages", [{}])[0]
            if not msg: continue
            sender = msg["from"]
            text   = msg["text"]["body"].lower().strip()

            reply = (
                "Render Bot LIVE!\n"
                "Verify token WORKS ✅\n\n"
                "Type:\n• hi\n• time\n• menu\n• ai what is love?"
            )
            if "hi" in text:
                reply = "Hello from Render! 🚀"
            elif "time" in text:
                reply = f"Time: {datetime.now():%H:%M:%S}"
            elif text.startswith("ai "):
                reply = f"AI heard: {text[3:]}"

            send(sender, reply)
    return "OK", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8000)))
