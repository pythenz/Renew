import nextcord
from nextcord.ext import commands
import os

intents = nextcord.Intents.default()
intents.members = True  # Required for member/role actions

bot = commands.Bot(command_prefix="!", intents=intents)

# Load all cogs
for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")

@bot.event
async def on_ready():
    await bot.sync_application_commands()  # Sync slash commands
    print(f"Logged in as {bot.user}")

# Run bot with your token
bot.run("YOUR_BOT_TOKEN")
