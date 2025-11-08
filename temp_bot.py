from flask import Flask, request
import requests, os, datetime
from dotenv import load_dotenv
load_dotenv()
from pyngrok import ngrok

app = Flask(__name__)
TOKEN    = os.getenv("TOKEN")      # paste Meta token
PHONE_ID = os.getenv("PHONE_ID")   # paste Phone ID

def send(to, text):
    requests.post(f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"messaging_product":"whatsapp", "to":to, "type":"text", "text":{"body":text}})

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == "tempbot":
        return request.args.get("hub.challenge")
    return "Wrong token", 403

@app.route("/webhook", methods=["POST"])
def hook():
    for entry in request.json.get("entry",[]):
        for change in entry.get("changes",[]):
            msg = change["value"].get("messages",[{}])[0]
            if not msg: continue
            sender = msg["from"]
            text   = msg["text"]["body"].lower().strip()

            if "hi" in text or "hello" in text:
                reply = "👋 Temp-Bot here!\nI’m Meta’s free number.\nWhat’s up?"
            elif "time" in text:
                reply = f"🕐 {datetime.datetime.now():%H:%M} on %{datetime.datetime.now():%b %d}"
            elif "menu" in text:
                reply = "🍔 Menu:\n1. Hi\n2. Time\n3. AI → ask anything!"
            else:
                reply = f"🤖 Echo: {text}\n(Type *menu*)"

            send(sender, reply)
    return "ok", 200

if __name__ == "__main__":
    public_url = ngrok.connect(5000, "http")
    print(f"NGROK URL: {public_url}")
    app.run(port=5000)