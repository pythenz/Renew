# main.py
import os
import nextcord
from nextcord.ext import commands
from nextcord import Intents
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8080))

intents = Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------
# Load Cogs
# -----------------------
cogs = ["cogs.moderation"]  # Add more cogs as they are ready
for cog in cogs:
    bot.load_extension(cog)

# -----------------------
# Slash command sync on ready
# -----------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} is online!")

# -----------------------
# Flask app for Render
# -----------------------
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

# Run Flask in background for Render
from threading import Thread

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

Thread(target=run_flask).start()

bot.run(TOKEN)
