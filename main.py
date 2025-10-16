import os
import threading
from flask import Flask
from dotenv import load_dotenv
from googletrans import Translator
import nextcord
from nextcord.ext import commands

# Load environment variables
load_dotenv()

# Flask setup
app = Flask(__name__)
translator = Translator()

@app.route("/")
def home():
    return "Bot + Flask API are running!"

@app.route("/translate", methods=["POST"])
def translate_text():
    from flask import request, jsonify
    data = request.get_json()
    text = data.get("text")
    target_lang = data.get("target")

    if not text or not target_lang:
        return jsonify({"error": "Missing text or target language"}), 400

    try:
        translated = translator.translate(text, dest=target_lang)
        return jsonify({"translated_text": translated.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def run_flask():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# Discord bot setup
intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# Run both Flask and Discord
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
