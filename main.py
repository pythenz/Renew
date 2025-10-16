from deep_translator import GoogleTranslator
import nextcord
from nextcord.ext import commands

@bot.command(name="translate")
async def translate(ctx, target_lang: str, *, text: str):
    """Translate text into a given language (auto-detect source)."""
    try:
        target_lang = target_lang.lower().strip()

        # Try the translation
        translated = GoogleTranslator(source="auto", target=target_lang).translate(text)

        # Format response
        response = f"**Translated to {target_lang.upper()}:**\n{translated}"

        # Split long messages into chunks (max 2000)
        if len(response) > 2000:
            parts = [response[i:i+2000] for i in range(0, len(response), 2000)]
            for part in parts:
                await ctx.send(part)
        else:
            await ctx.send(response)

    except Exception as e:
        err_msg = f"❌ Translation failed: {e}"

        # If the error is too long, send as file
        if len(err_msg) > 2000:
            with open("error.txt", "w") as f:
                f.write(str(e))
            await ctx.send("Error message too long — sent as file instead:", file=nextcord.File("error.txt"))
        else:
            await ctx.send(err_msg)
