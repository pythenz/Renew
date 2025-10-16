import os
import nextcord
from nextcord.ext import commands
from deep_translator import GoogleTranslator
from keep_alive import keep_alive  # Flask server for uptime

# Load environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("PREFIX", "!")  # Default to "!" if not set

# Bot setup
intents = nextcord.Intents.default()
intents.message_content = True  # Needed for reading message content

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Start keep_alive Flask server
keep_alive()

# -------------------
# Bot Events
# -------------------
@bot.event
async def on_ready():
    print(f"{bot.user} is online!")

# -------------------
# Example Commands
# -------------------

# Ping command
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# Translate command
@bot.command()
async def translate(ctx, target_language: str, *, text: str):
    """
    Usage: !translate <target_language> <text>
    Example: !translate es Hello world
    """
    try:
        translated_text = GoogleTranslator(source='auto', target=target_language).translate(text)
        await ctx.send(f"**Translated:** {translated_text}")
    except Exception as e:
        await ctx.send(f"Error translating text: {e}")

# Add more commands here...

# -------------------
# Run bot
# -------------------
bot.run(TOKEN)
