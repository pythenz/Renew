import os
import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# -----------------------
# Flask Web Server (Keep Alive)
# -----------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# -----------------------
# Bot Setup
# -----------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------
# Events
# -----------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.change_presence(activity=nextcord.Game("Moderating the server!"))

# -----------------------
# Cog Loader
# -----------------------
initial_extensions = ["cogs.moderation"]

if __name__ == "__main__":
    for ext in initial_extensions:
        try:
            bot.load_extension(ext)
            print(f"Loaded {ext}")
        except Exception as e:
            print(f"Failed to load {ext}: {e}")

    # Run Flask in background
    Thread(target=run_web).start()

    # Run Discord bot
    bot.run(TOKEN)
