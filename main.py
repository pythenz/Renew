import nextcord
from nextcord.ext import commands
from nextcord import Interaction, Embed
import os
from flask import Flask

# -----------------------
# Flask Webserver (for Render)
# -----------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

# -----------------------
# Bot Initialization
# -----------------------
intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True  # Needed for prefix commands
bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------
# Gothic Help Cog
# -----------------------
class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        embed = Embed(
            title="🦇 Shadows of Commands 🦇",
            description="Darkness awaits, mortal. Choose your path wisely...",
            color=0x1C1C1C
        )
        for cog_name, cog in self.bot.cogs.items():
            commands_list = cog.get_commands()
            if commands_list:
                desc = ""
                for command in commands_list:
                    if not command.hidden:
                        desc += f"**{ctx.prefix}{command.name}** - {command.help or 'No description'}\n"
                if desc:
                    embed.add_field(name=f"⚔️ {cog_name}", value=desc, inline=False)
        embed.set_footer(text="Use commands with caution...")
        await ctx.send(embed=embed)

    @nextcord.slash_command(name="help", description="Show all commands")
    async def help_slash(self, interaction: Interaction):
        embed = Embed(
            title="🦇 Shadows of Commands 🦇",
            description="Darkness awaits, mortal. Choose your path wisely...",
            color=0x1C1C1C
        )
        for cog_name, cog in self.bot.cogs.items():
            commands_list = cog.get_commands()
            if commands_list:
                desc = ""
                for command in commands_list:
                    if not command.hidden:
                        desc += f"**/{command.name}** - {command.help or 'No description'}\n"
                if desc:
                    embed.add_field(name=f"⚔️ {cog_name}", value=desc, inline=False)
        embed.set_footer(text="Use commands with caution...")
        await interaction.response.send_message(embed=embed, ephemeral=True)

# -----------------------
# Load Cogs
# -----------------------
bot.add_cog(HelpCog(bot))
bot.load_extension("cogs.moderation")  # Make sure moderation.py is in cogs/

# -----------------------
# Run Flask + Bot
# -----------------------
if __name__ == "__main__":
    import threading

    def run_flask():
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

    threading.Thread(target=run_flask).start()
    bot.run(os.environ.get("TOKEN"))
