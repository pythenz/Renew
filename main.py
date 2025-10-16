import os
from threading import Thread
from flask import Flask
import nextcord
from nextcord.ext import commands
from deep_translator import GoogleTranslator

# ---------------- Flask for Render ----------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))  # Render sets the PORT
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask).start()

# ---------------- Discord Bot ----------------
intents = nextcord.Intents.default()
intents.message_content = True  # Needed for prefix commands & replies

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- Supported Languages ----------------
# Fetch from GoogleTranslator instance
translator_instance = GoogleTranslator(source="auto", target="en")  # just dummy instance
SUPPORTED_LANGS = GoogleTranslator.get_supported_languages(as_dict=True)

# ---------------- Events ----------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ---------------- Translate Command ----------------
@bot.slash_command(name="translate", description="Translate a message")
@bot.command(name="translate")  # Prefix command
async def translate(ctx, target_lang: str, *, text: str = None):
    try:
        # If user replied to a message and no text provided, use that message
        if isinstance(ctx, nextcord.Interaction):
            msg = ctx.message if hasattr(ctx, "message") else None
        else:
            msg = ctx.message.reference.resolved if ctx.message.reference else None

        if not text and msg:
            text = msg.content

        if not text:
            await ctx.send("You must provide text or reply to a message!", ephemeral=True if isinstance(ctx, nextcord.Interaction) else False)
            return

        target_lang = target_lang.lower()
        if target_lang not in SUPPORTED_LANGS and target_lang not in SUPPORTED_LANGS.values():
            await ctx.send(f"Unsupported language: `{target_lang}`")
            return

        translated = GoogleTranslator(source="auto", target=target_lang).translate(text)

        # Discord limit
        if len(translated) > 2000:
            translated = translated[:1997] + "..."

        await ctx.send(f"**Translated ({target_lang}):** {translated}")

    except Exception as e:
        await ctx.send(f"Error translating: {e}")

# ---------------- Run Bot ----------------
bot.run(os.environ["DISCORD_TOKEN"])
