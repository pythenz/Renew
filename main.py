import os
import nextcord
from nextcord.ext import commands
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

# Load .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# === Flask Keep-Alive Server ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

# === Discord Bot Setup ===
intents = nextcord.Intents.default()
intents.message_content = True  # needed for prefix commands
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# Example test command
@bot.slash_command(name="ping", description="Replies with pong!")
async def ping_slash(interaction: nextcord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

@bot.command(name="ping")
async def ping_prefix(ctx):
    await ctx.send("🏓 Pong!")

# === Run both Flask + Bot ===
if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(TOKEN)
