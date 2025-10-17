import nextcord
from nextcord.ext import commands, tasks
from nextcord import Intents
import os
from keep_alive import keep_alive  # assuming you have a keep_alive.py for Render

# ---------------------------
# Bot Setup
# ---------------------------
intents = Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,  # optional: remove default help
)

# ---------------------------
# Load Cogs
# ---------------------------
for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")

# ---------------------------
# Events
# ---------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} | ID: {bot.user.id}")
    print("------")

# ---------------------------
# Keep Alive (Flask) for Render
# ---------------------------
keep_alive()  # starts the Flask app

# ---------------------------
# Run Bot
# ---------------------------
TOKEN = os.getenv("DISCORD_TOKEN")  # put your bot token in Render environment variables
bot.run(TOKEN)
