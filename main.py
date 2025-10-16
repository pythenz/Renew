import nextcord
from nextcord.ext import commands
from deep_translator import GoogleTranslator
from flask import Flask
import threading, os

# ---------- Flask keep-alive ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ---------- Bot Setup ----------
intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- Translator Setup ----------
translator_instance = GoogleTranslator(source="auto", target="en")
SUPPORTED_LANGS = translator_instance.get_supported_languages(as_dict=True)
LANG_CODES = {v: k for k, v in SUPPORTED_LANGS.items()}

def translate_text(text: str, target_lang: str) -> str:
    translator = GoogleTranslator(source="auto", target=target_lang)
    return translator.translate(text)

# ---------- Prefix Command ----------
@bot.command(name="translate")
async def translate_prefix(ctx, target_lang: str):
    if ctx.message.reference:
        ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        text_to_translate = ref_msg.content
    else:
        await ctx.send("Please reply to a message to translate.")
        return

    target_lang = target_lang.lower()
    if target_lang not in LANG_CODES:
        await ctx.send(f"Language not supported! Supported: {', '.join(SUPPORTED_LANGS.keys())}")
        return

    try:
        translated = translate_text(text_to_translate, target_lang)
        await ctx.send(f"**Translated ({LANG_CODES[target_lang]}):** {translated}")
    except Exception as e:
        await ctx.send(f"Error translating text: {e}")

# ---------- Slash Command ----------
@bot.slash_command(name="translate", description="Translate a message")
async def translate_slash(interaction: nextcord.Interaction, target_lang: str):
    if not interaction.message.reference:
        await interaction.response.send_message("Reply to a message to translate.", ephemeral=True)
        return

    ref_msg = await interaction.channel.fetch_message(interaction.message.reference.message_id)
    text_to_translate = ref_msg.content

    target_lang = target_lang.lower()
    if target_lang not in LANG_CODES:
        await interaction.response.send_message(f"Language not supported! Supported: {', '.join(SUPPORTED_LANGS.keys())}", ephemeral=True)
        return

    try:
        translated = translate_text(text_to_translate, target_lang)
        await interaction.response.send_message(f"**Translated ({LANG_CODES[target_lang]}):** {translated}")
    except Exception as e:
        await interaction.response.send_message(f"Error translating text: {e}", ephemeral=True)

# ---------- Run ----------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
