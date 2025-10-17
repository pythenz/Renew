import os
import nextcord
from nextcord.ext import commands, tasks
from flask import Flask
import asyncio

# -----------------------
# Flask Web Service
# -----------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# -----------------------
# Bot Setup
# -----------------------
intents = nextcord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True  # Needed for on_message

bot = commands.Bot(
    command_prefix="!", 
    intents=intents, 
    help_command=None  # Disable default help
)

# -----------------------
# Load Cogs
# -----------------------
COG_PATH = "apps.cogs"
cogs = ["moderation", "rr", "help_cog"]  # Add other cogs here

for cog in cogs:
    try:
        bot.load_extension(f"{COG_PATH}.{cog}")
        print(f"Loaded {cog}")
    except Exception as e:
        print(f"Failed to load cog {cog}: {e}")

# -----------------------
# Events
# -----------------------
@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

# -----------------------
# Run Both Flask & Bot
# -----------------------
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(asyncio.to_thread(run_flask))
    bot.run(os.environ.get("DISCORD_TOKEN"))
