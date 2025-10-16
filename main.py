import os
from dotenv import load_dotenv
import nextcord
from nextcord.ext import commands
from deep_translator import GoogleTranslator

load_dotenv()

intents = nextcord.Intents.default()
intents.message_content = True  # needed for prefix commands
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")

# Supported languages
SUPPORTED_LANGS = GoogleTranslator().get_supported_languages(as_dict=True)  # get dict {lang_name: code}

# -------------------------------
# Prefix Command
# -------------------------------
@bot.command(name="translate")
async def translate_prefix(ctx, target_language: str, *, text: str = None):
    # If user replied to a message and didn't provide text, grab it
    if text is None and ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        text = ref.content
    
    if text is None:
        await ctx.send("Please provide text to translate or reply to a message!")
        return

    lang_code = SUPPORTED_LANGS.get(target_language.lower())
    if not lang_code:
        await ctx.send(f"Unsupported language! Supported: {', '.join(SUPPORTED_LANGS.keys())}")
        return

    try:
        translated = GoogleTranslator(source='auto', target=lang_code).translate(text)
        if len(translated) > 2000:
            translated = translated[:1997] + "..."
        await ctx.send(translated)
    except Exception as e:
        await ctx.send(f"Error translating text: {e}")


# -------------------------------
# Slash Command
# -------------------------------
@bot.slash_command(name="translate", description="Translate a message to a language of your choice")
async def translate_slash(
    interaction: nextcord.Interaction,
    target_language: str,
    message: str = None
):
    # Grab replied-to message if no text provided
    if message is None and interaction.message:
        message = interaction.message.content

    if message is None:
        await interaction.response.send_message("Please provide text or reply to a message!", ephemeral=True)
        return

    lang_code = SUPPORTED_LANGS.get(target_language.lower())
    if not lang_code:
        await interaction.response.send_message(
            f"Unsupported language! Supported: {', '.join(SUPPORTED_LANGS.keys())}", ephemeral=True
        )
        return

    try:
        translated = GoogleTranslator(source='auto', target=lang_code).translate(message)
        if len(translated) > 2000:
            translated = translated[:1997] + "..."
        await interaction.response.send_message(translated)
    except Exception as e:
        await interaction.response.send_message(f"Error translating text: {e}", ephemeral=True)


bot.run(TOKEN)
