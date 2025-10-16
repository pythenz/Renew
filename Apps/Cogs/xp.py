from nextcord.ext import commands

class XP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(XP(bot))
