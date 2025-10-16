import nextcord
from nextcord.ext import commands
from deep_translator import GoogleTranslator
from nextcord import Interaction, SlashOption

intents = nextcord.Intents.default()
intents.message_content = True  # needed for prefix commands
bot = commands.Bot(command_prefix="!", intents=intents)

# Create a translator instance for fetching supported languages
translator = GoogleTranslator()
SUPPORTED_LANGS = translator.get_supported_languages(as_dict=True)  # {'english': 'en', ...}

def get_lang_code(lang_name: str):
    """Get language code from user input (case insensitive)."""
    return SUPPORTED_LANGS.get(lang_name.lower())

# ---------------- Prefix Command ----------------
@bot.command(name="translate")
async def translate_prefix(ctx, target_lang: str, *, text: str = None):
    try:
        # If user is replying to a message and text not provided, use replied content
        if text is None and ctx.message.reference:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            text = ref_msg.content
        elif text is None:
            await ctx.send("Please provide text to translate or reply to a message.")
            return

        target_code = get_lang_code(target_lang)
        if not target_code:
            await ctx.send(f"Language `{target_lang}` not supported.")
            return

        translated = GoogleTranslator(source='auto', target=target_code).translate(text)
        # Discord max length is 2000
        if len(translated) > 2000:
            translated = translated[:1997] + "..."
        await ctx.send(translated)
    except Exception as e:
        await ctx.send(f"Error translating text: {e}")

# ---------------- Slash Command ----------------
@bot.slash_command(name="translate", description="Translate text to a language")
async def translate_slash(
    interaction: Interaction,
    target_lang: str = SlashOption(
        description="Target language",
        choices={lang: code for lang, code in SUPPORTED_LANGS.items()}
    ),
    text: str = SlashOption(description="Text to translate", required=False)
):
    try:
        # If replying to a message and no text provided
        if text is None and interaction.message:
            text = interaction.message.content
        elif text is None:
            await interaction.response.send_message("Please provide text to translate or reply to a message.")
            return

        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        if len(translated) > 2000:
            translated = translated[:1997] + "..."
        await interaction.response.send_message(translated)
    except Exception as e:
        await interaction.response.send_message(f"Error translating text: {e}")

# ---------------- Run Bot ----------------
bot.run("YOUR_TOKEN_HERE")
