import nextcord
from nextcord.ext import commands
from config import BOT_NAME, DISCORD_TOKEN
import os

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Automatically load all cogs in cogs folder
cogs_dir = os.path.join(os.path.dirname(__file__), "app", "cogs")
if os.path.exists(cogs_dir):
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py"):
            cog_name = filename[:-3]  # remove .py
            try:
                bot.load_extension(f"app.cogs.{cog_name}")
                print(f"Loaded cog: {cog_name}")
            except Exception as e:
                print(f"Failed to load {cog_name}: {e}")
else:
    print("ERROR: cogs folder not found!")

@bot.event
async def on_ready():
    print(f"{BOT_NAME} is online as {bot.user}!")

def run_bot():
    bot.run(DISCORD_TOKEN)
