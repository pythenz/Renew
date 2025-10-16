from flask import Flask
import os
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Renew bot is alive!"

def run():
    port = int(os.environ.get("PORT", 10000))
    print(f"Flask server running on port {port}")
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    server = Thread(target=run)
    server.daemon = True
    server.start()
