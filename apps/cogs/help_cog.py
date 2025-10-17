import nextcord
from nextcord.ext import commands, tasks

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        # Define pages
        pages = [
            "🗡️ **Moderation Commands**\n`kick`, `ban`, `mute`, `unmute`, `purge`, `automod` toggle",
            "⚔️ **Reaction Roles**\n`rr_setup`, `rr_add`, `rr_remove`",
            "🛡️ **Levels & XP**\n`level`, `leaderboard`, `set_xp_rate`",
            "📜 **Tickets & Forms**\n`ticket`, `close_ticket`, `form`, `submit_form`",
            "📊 **Server Utilities**\n`suggest`, `poll`, `stats`"
        ]

        current_page = 0
        msg = await ctx.send(pages[current_page])

        # Add navigation reactions
        await msg.add_reaction("⬅️")
        await msg.add_reaction("➡️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == msg.id

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=120.0, check=check)

                if str(reaction.emoji) == "⬅️":
                    current_page = (current_page - 1) % len(pages)
                elif str(reaction.emoji) == "➡️":
                    current_page = (current_page + 1) % len(pages)

                await msg.edit(content=pages[current_page])
                await msg.remove_reaction(reaction.emoji, user)

            except nextcord.ext.commands.errors.CommandInvokeError:
                break  # Stop if message deleted
            except Exception:
                break  # Timeout or other issues

def setup(bot):
    bot.add_cog(HelpCog(bot))
