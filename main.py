import nextcord
from nextcord.ext import commands
from deep_translator import GoogleTranslator
import os

intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# --- SLASH COMMAND ---
@bot.slash_command(name="translate", description="Translate text into another language")
async def translate_slash(interaction: nextcord.Interaction, text: str, target_language: str):
    try:
        translated = GoogleTranslator(source='auto', target=target_language).translate(text)
        if len(translated) > 1900:
            translated = translated[:1900] + "..."
        await interaction.response.send_message(
            f"**Translated ({target_language}):**\n{translated}"
        )
    except Exception as e:
        err_msg = str(e)
        if len(err_msg) > 1900:
            err_msg = err_msg[:1900] + "..."
        await interaction.response.send_message(f"⚠️ Error translating text: {err_msg}")

# --- PREFIX COMMAND ---
@bot.command(name="translate")
async def translate_prefix(ctx, target_language: str, *, text: str):
    try:
        translated = GoogleTranslator(source='auto', target=target_language).translate(text)
        if len(translated) > 1900:
            translated = translated[:1900] + "..."
        await ctx.send(f"**Translated ({target_language}):**\n{translated}")
    except Exception as e:
        err_msg = str(e)
        if len(err_msg) > 1900:
            err_msg = err_msg[:1900] + "..."
        await ctx.send(f"⚠️ Error translating text: {err_msg}")

# --- run bot ---
bot.run(os.getenv("DISCORD_TOKEN"))
