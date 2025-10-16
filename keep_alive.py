from flask import Flask
from threading import Thread
import os

app = Flask("keep_alive")

@app.route("/")
def home():
    return "Renew Bot is alive!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
