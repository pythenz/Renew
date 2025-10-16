import nextcord
from nextcord.ext import commands
from deep_translator import GoogleTranslator
from nextcord import Interaction, SlashOption

intents = nextcord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# List of supported languages
SUPPORTED_LANGS = GoogleTranslator.get_supported_languages(as_dict=True)

async def translate_text(text: str, target: str):
    target = target.lower()
    if target not in SUPPORTED_LANGS:
        raise ValueError(f"Language '{target}' not supported.")
    return GoogleTranslator(source='auto', target=SUPPORTED_LANGS[target]).translate(text)

# ---------------- Prefix Command ----------------
@bot.command(name="translate")
async def translate_prefix(ctx, *, args=None):
    # Check if user replied to a message
    if ctx.message.reference:
        message_to_translate = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        text = message_to_translate.content
        # Parse language from args (e.g., !translate french)
        if not args:
            await ctx.send("Please provide a target language, e.g., `!translate french`.")
            return
        target_lang = args.strip()
    else:
        if not args or " to " not in args:
            await ctx.send("Usage: `!translate <text> to <language>`")
            return
        text, target_lang = args.rsplit(" to ", 1)
    
    try:
        translated = await translate_text(text, target_lang)
        # Handle Discord message length limit
        if len(translated) > 2000:
            translated = translated[:1997] + "..."
        await ctx.send(f"**Translated ({target_lang}):** {translated}")
    except Exception as e:
        await ctx.send(f"Error: {e}")

# ---------------- Slash Command ----------------
@bot.slash_command(name="translate", description="Translate a message or text to another language")
async def translate_slash(
    interaction: Interaction,
    text: str = SlashOption(name="text", description="Text to translate", required=False),
    target: str = SlashOption(name="to", description="Language to translate to", required=True)
):
    # If user replied to a message
    if interaction.message and interaction.message.reference and not text:
        ref_msg = await interaction.channel.fetch_message(interaction.message.reference.message_id)
        text = ref_msg.content
    
    if not text:
        await interaction.response.send_message("No text to translate.", ephemeral=True)
        return
    
    try:
        translated = await translate_text(text, target)
        if len(translated) > 2000:
            translated = translated[:1997] + "..."
        await interaction.response.send_message(f"**Translated ({target}):** {translated}")
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}", ephemeral=True)

bot.run("YOUR_TOKEN_HERE")
