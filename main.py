import os
from threading import Thread
from flask import Flask
import nextcord
from nextcord.ext import commands

# ----------------- FLASK SETUP -----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is online!"

def run_web():
    port = int(os.environ.get("PORT", 8080))  # Render assigns this port
    app.run(host="0.0.0.0", port=port)

# Run Flask in a background thread so the bot can run too
Thread(target=run_web).start()

# ----------------- DISCORD BOT SETUP -----------------
intents = nextcord.Intents.default()
intents.message_content = True  # required for prefix commands

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------- EXAMPLE COMMANDS -----------------
@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")

@bot.slash_command(name="ping")
async def ping_slash(interaction: nextcord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.command(name="say")
async def say(ctx, *, message: str):
    await ctx.send(message)

@bot.slash_command(name="say")
async def say_slash(interaction: nextcord.Interaction, message: str):
    await interaction.response.send_message(message)

# ----------------- RUN BOT -----------------
TOKEN = os.environ.get("DISCORD_TOKEN")  # store your token in Render env vars
bot.run(TOKEN)
