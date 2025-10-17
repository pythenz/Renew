import nextcord
from nextcord.ext import commands, tasks
from nextcord.utils import get
from nextcord import Permissions
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_mod_enabled = True
        self.banned_words = ["badword1", "badword2"]
        self.invite_block = True
        self.mod_roles = ["Moderator", "Admin"]

    # -----------------------
    # Helper Functions
    # -----------------------
    def has_mod_role(self, member: nextcord.Member):
        return any(role.name in self.mod_roles for role in member.roles)

    async def log_action(self, ctx_or_interaction, message: str):
        log_channel = get(ctx_or_interaction.guild.text_channels, name="mod-log")
        if log_channel:
            await log_channel.send(message)

    # -----------------------
    # Auto-moderation
    # -----------------------
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not self.auto_mod_enabled:
            return
        if self.has_mod_role(message.author):
            return

        # Banned words
        for word in self.banned_words:
            if word.lower() in message.content.lower():
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention}, watch your language!", delete_after=5
                )
                return

        # Invite links
        if self.invite_block and ("discord.gg/" in message.content.lower() or "discord.com/invite/" in message.content.lower()):
            await message.delete()
            await message.channel.send(
                f"{message.author.mention}, invites are not allowed!", delete_after=5
            )
            return

    # -----------------------
    # Auto-mod toggle
    # -----------------------
    async def _toggle_auto_mod(self, ctx_or_interaction, state: str):
        user = ctx_or_interaction.author if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user
        send_func = ctx_or_interaction.send if hasattr(ctx_or_interaction, 'send') else ctx_or_interaction.response.send_message
        if not self.has_mod_role(user):
            return await send_func("No permission.", ephemeral=True)
        if state.lower() not in ["on", "off"]:
            return await send_func("Use 'on' or 'off'.", ephemeral=True)
        self.auto_mod_enabled = state.lower() == "on"
        await send_func(f"Auto-moderation is now {state.upper()}.", ephemeral=True)
        await self.log_action(ctx_or_interaction, f"Auto-moderation toggled {state.upper()} by {user}.")

    @commands.command(name="automod")
    async def toggle_auto_mod(self, ctx, state: str):
        await self._toggle_auto_mod(ctx, state)

    @nextcord.slash_command(name="automod", description="Toggle auto moderation")
    async def toggle_auto_mod_slash(self, interaction: nextcord.Interaction, state: str):
        await self._toggle_auto_mod(interaction, state)

    # -----------------------
    # Banned words
    # -----------------------
    async def _add_banned_word(self, ctx_or_interaction, word: str):
        user = ctx_or_interaction.author if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user
        send_func = ctx_or_interaction.send if hasattr(ctx_or_interaction, 'send') else ctx_or_interaction.response.send_message
        if not self.has_mod_role(user):
            return await send_func("No permission.", ephemeral=True)
        if word.lower() in self.banned_words:
            return await send_func("Word already banned.", ephemeral=True)
        self.banned_words.append(word.lower())
        await send_func(f"Added '{word}' to banned words.", ephemeral=True)
        await self.log_action(ctx_or_interaction, f"{user} added '{word}' to banned words.")

    async def _remove_banned_word(self, ctx_or_interaction, word: str):
        user = ctx_or_interaction.author if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user
        send_func = ctx_or_interaction.send if hasattr(ctx_or_interaction, 'send') else ctx_or_interaction.response.send_message
        if not self.has_mod_role(user):
            return await send_func("No permission.", ephemeral=True)
        try:
            self.banned_words.remove(word.lower())
            await send_func(f"Removed '{word}' from banned words.", ephemeral=True)
            await self.log_action(ctx_or_interaction, f"{user} removed '{word}' from banned words.")
        except ValueError:
            await send_func("Word not found.", ephemeral=True)

    @commands.command(name="addword")
    async def add_banned_word(self, ctx, *, word: str):
        await self._add_banned_word(ctx, word)

    @nextcord.slash_command(name="addword", description="Add a banned word")
    async def add_banned_word_slash(self, interaction: nextcord.Interaction, word: str):
        await self._add_banned_word(interaction, word)

    @commands.command(name="removeword")
    async def remove_banned_word(self, ctx, *, word: str):
        await self._remove_banned_word(ctx, word)

    @nextcord.slash_command(name="removeword", description="Remove a banned word")
    async def remove_banned_word_slash(self, interaction: nextcord.Interaction, word: str):
        await self._remove_banned_word(interaction, word)

    # -----------------------
    # Kick, Ban, Mute/Unmute
    # -----------------------
    async def _kick(self, ctx_or_interaction, member: nextcord.Member, *, reason=None):
        user = ctx_or_interaction.author if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user
        send_func = ctx_or_interaction.send if hasattr(ctx_or_interaction, 'send') else ctx_or_interaction.response.send_message
        if not self.has_mod_role(user):
            return await send_func("No permission.", ephemeral=True)
        try:
            await member.kick(reason=reason)
            await send_func(f"{member} has been kicked.", ephemeral=True)
            await self.log_action(ctx_or_interaction, f"{user} kicked {member}. Reason: {reason}")
        except Exception as e:
            await send_func(f"Failed to kick: {e}", ephemeral=True)

    async def _ban(self, ctx_or_interaction, member: nextcord.Member, *, reason=None):
        user = ctx_or_interaction.author if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user
        send_func = ctx_or_interaction.send if hasattr(ctx_or_interaction, 'send') else ctx_or_interaction.response.send_message
        if not self.has_mod_role(user):
            return await send_func("No permission.", ephemeral=True)
        try:
            await member.ban(reason=reason)
            await send_func(f"{member} has been banned.", ephemeral=True)
            await self.log_action(ctx_or_interaction, f"{user} banned {member}. Reason: {reason}")
        except Exception as e:
            await send_func(f"Failed to ban: {e}", ephemeral=True)

    async def _mute(self, ctx_or_interaction, member: nextcord.Member, duration: int = 0):
        user = ctx_or_interaction.author if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user
        send_func = ctx_or_interaction.send if hasattr(ctx_or_interaction, 'send') else ctx_or_interaction.response.send_message
        if not self.has_mod_role(user):
            return await send_func("No permission.", ephemeral=True)
        role = get(ctx_or_interaction.guild.roles, name="Muted")
        if not role:
            role = await ctx_or_interaction.guild.create_role(name="Muted", permissions=Permissions(send_messages=False))
            for channel in ctx_or_interaction.guild.channels:
                await channel.set_permissions(role, send_messages=False)
        await member.add_roles(role)
        await send_func(f"{member} has been muted.", ephemeral=True)
        await self.log_action(ctx_or_interaction, f"{user} muted {member}. Duration: {duration}s")
        if duration > 0:
            await asyncio.sleep(duration)
            await member.remove_roles(role)
            await ctx_or_interaction.channel.send(f"{member} has been auto-unmuted after {duration}s")
            await self.log_action(ctx_or_interaction, f"{member} auto-unmuted after {duration}s")

    async def _unmute(self, ctx_or_interaction, member: nextcord.Member):
        user = ctx_or_interaction.author if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user
        send_func = ctx_or_interaction.send if hasattr(ctx_or_interaction, 'send') else ctx_or_interaction.response.send_message
        if not self.has_mod_role(user):
            return await send_func("No permission.", ephemeral=True)
        role = get(ctx_or_interaction.guild.roles, name="Muted")
        if role in member.roles:
            await member.remove_roles(role)
            await send_func(f"{member} has been unmuted.", ephemeral=True)
            await self.log_action(ctx_or_interaction, f"{user} unmuted {member}.")
        else:
            await send_func(f"{member} is not muted.", ephemeral=True)

    @commands.command(name="kick")
    async def kick(self, ctx, member: nextcord.Member, *, reason=None):
        await self._kick(ctx, member, reason=reason)

    @nextcord.slash_command(name="kick", description="Kick a member")
    async def kick_slash(self, interaction: nextcord.Interaction, member: nextcord.Member, reason: str = None):
        await self._kick(interaction, member, reason=reason)

    @commands.command(name="ban")
    async def ban(self, ctx, member: nextcord.Member, *, reason=None):
        await self._ban(ctx, member, reason=reason)

    @nextcord.slash_command(name="ban", description="Ban a member")
    async def ban_slash(self, interaction: nextcord.Interaction, member: nextcord.Member, reason: str = None):
        await self._ban(interaction, member, reason=reason)

    @commands.command(name="mute")
    async def mute(self, ctx, member: nextcord.Member, duration: int = 0):
        await self._mute(ctx, member, duration)

    @nextcord.slash_command(name="mute", description="Mute a member")
    async def mute_slash(self, interaction: nextcord.Interaction, member: nextcord.Member, duration: int = 0):
        await self._mute(interaction, member, duration)

    @commands.command(name="unmute")
    async def unmute(self, ctx, member: nextcord.Member):
        await self._unmute(ctx, member)

    @nextcord.slash_command(name="unmute", description="Unmute a member")
    async def unmute_slash(self, interaction: nextcord.Interaction, member: nextcord.Member):
        await self._unmute(interaction, member)

    # -----------------------
    # Purge messages
    # -----------------------
    async def _purge(self, ctx_or_interaction, amount: int):
        user = ctx_or_interaction.author if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user
        send_func = ctx_or_interaction.send if hasattr(ctx_or_interaction, 'send') else ctx_or_interaction.response.send_message
        if not self.has_mod_role(user):
            return await send_func("No permission.", ephemeral=True)
        deleted = await ctx_or_interaction.channel.purge(limit=amount)
        await ctx_or_interaction.channel.send(f"Deleted {len(deleted)} messages.", delete_after=5)
        await self.log_action(ctx_or_interaction, f"{user} purged {len(deleted)} messages in {ctx_or_interaction.channel}.")

    @commands.command(name="purge")
    async def purge(self, ctx, amount: int):
        await self._purge(ctx, amount)

    @nextcord.slash_command(name="purge", description="Purge messages")
    async def purge_slash(self, interaction: nextcord.Interaction, amount: int):
        await self._purge(interaction, amount)


def setup(bot):
    bot.add_cog(Moderation(bot))
