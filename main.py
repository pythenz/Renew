# main.py
import os
import nextcord
from nextcord.ext import commands, tasks
from flask import Flask
from threading import Thread

# -----------------------
# Flask for Render keep-alive
# -----------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# -----------------------
# Bot setup
# -----------------------
intents = nextcord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)  # Removed default help

# -----------------------
# Load cogs
# -----------------------
initial_cogs = [
    "cogs.moderation",
    "cogs.rr",          # Reaction role cog
    "cogs.help_cog",    # Gothic reaction-based help
    # Add more cogs here as you build them
]

for cog in initial_cogs:
    try:
        bot.load_extension(cog)
        print(f"Loaded cog: {cog}")
    except Exception as e:
        print(f"Failed to load cog {cog}: {e}")

# -----------------------
# Events
# -----------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    print("------")

# -----------------------
# Background Flask thread for Render
# -----------------------
flask_thread = Thread(target=run_flask)
flask_thread.start()

# -----------------------
# Run bot
# -----------------------
TOKEN = os.environ.get("DISCORD_TOKEN")  # Store your bot token in Render's environment variables
bot.run(TOKEN)
