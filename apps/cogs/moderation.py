import nextcord
from nextcord.ext import commands, tasks
from nextcord.utils import get
from nextcord import Permissions
import asyncio
import datetime

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_mod_enabled = True
        self.banned_words = ["badword1", "badword2"]
        self.invite_block = True
        self.mod_roles = ["Moderator", "Admin"]
        self.bypass_roles = []  # roles that bypass auto-mod
        self.temp_bans = {}  # {user_id: unban_time}
        self.temp_mutes = {}  # {user_id: (unmute_time, guild_id)}

    # -----------------------
    # Helpers
    # -----------------------
    def has_mod_role(self, member: nextcord.Member):
        return any(role.name in self.mod_roles for role in member.roles)

    def has_bypass_role(self, member: nextcord.Member):
        return any(role.name in self.bypass_roles for role in member.roles)

    async def log_action(self, ctx_or_guild, message):
        guild = ctx_or_guild.guild if hasattr(ctx_or_guild, 'guild') else ctx_or_guild
        log_channel = get(guild.text_channels, name="mod-log")
        if log_channel:
            await log_channel.send(message)

    # -----------------------
    # Auto-moderation
    # -----------------------
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not self.auto_mod_enabled:
            return
        if self.has_mod_role(message.author) or self.has_bypass_role(message.author):
            return

        for word in self.banned_words:
            if word.lower() in message.content.lower():
                await message.delete()
                await message.channel.send(f"{message.author.mention}, watch your language!", delete_after=5)
                await self.log_action(message, f"Deleted message from {message.author}: contained banned word '{word}'")
                return

        if self.invite_block and ("discord.gg/" in message.content.lower() or "discord.com/invite/" in message.content.lower()):
            await message.delete()
            await message.channel.send(f"{message.author.mention}, invites are not allowed!", delete_after=5)
            await self.log_action(message, f"Deleted invite message from {message.author}")
            return

    # -----------------------
    # Message edit/delete tracking
    # -----------------------
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        await self.log_action(message.guild, f"Message deleted in {message.channel} by {message.author}: {message.content}")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        await self.log_action(before.guild, f"Message edited in {before.channel} by {before.author}:\nBefore: {before.content}\nAfter: {after.content}")

    # -----------------------
    # Auto-mod toggle
    # -----------------------
    @commands.command(name="automod")
    async def toggle_auto_mod(self, ctx, state: str):
        if not self.has_mod_role(ctx.author):
            return await ctx.send("No permission.")
        if state.lower() not in ["on", "off"]:
            return await ctx.send("Use 'on' or 'off'.")
        self.auto_mod_enabled = state.lower() == "on"
        await ctx.send(f"Auto-moderation is now {state.upper()}.")
        await self.log_action(ctx, f"Auto-moderation toggled {state.upper()} by {ctx.author}.")

    @nextcord.slash_command(name="automod", description="Toggle auto moderation")
    async def toggle_auto_mod_slash(self, interaction: nextcord.Interaction, state: str):
        if not self.has_mod_role(interaction.user):
            return await interaction.response.send_message("No permission.", ephemeral=True)
        if state.lower() not in ["on", "off"]:
            return await interaction.response.send_message("Use 'on' or 'off'.", ephemeral=True)
        self.auto_mod_enabled = state.lower() == "on"
        await interaction.response.send_message(f"Auto-moderation is now {state.upper()}.", ephemeral=True)
        await self.log_action(interaction, f"Auto-moderation toggled {state.upper()} by {interaction.user}.")

    # -----------------------
    # Manage banned words
    # -----------------------
    @commands.command(name="addword")
    async def add_banned_word(self, ctx, *, word: str):
        if not self.has_mod_role(ctx.author):
            return await ctx.send("No permission.")
        if word.lower() in self.banned_words:
            return await ctx.send("Word already banned.")
        self.banned_words.append(word.lower())
        await ctx.send(f"Added '{word}' to banned words.")
        await self.log_action(ctx, f"{ctx.author} added '{word}' to banned words.")

    @commands.command(name="removeword")
    async def remove_banned_word(self, ctx, *, word: str):
        if not self.has_mod_role(ctx.author):
            return await ctx.send("No permission.")
        try:
            self.banned_words.remove(word.lower())
            await ctx.send(f"Removed '{word}' from banned words.")
            await self.log_action(ctx, f"{ctx.author} removed '{word}' from banned words.")
        except ValueError:
            await ctx.send("Word not found in banned list.")

    # -----------------------
    # Manage mod roles
    # -----------------------
    @commands.command(name="addmodrole")
    async def add_mod_role(self, ctx, *, role_name: str):
        if not self.has_mod_role(ctx.author):
            return await ctx.send("No permission.")
        if role_name in self.mod_roles:
            return await ctx.send("Role already a mod role.")
        self.mod_roles.append(role_name)
        await ctx.send(f"Added '{role_name}' as a mod role.")
        await self.log_action(ctx, f"{ctx.author} added '{role_name}' to mod roles.")

    @commands.command(name="removemodrole")
    async def remove_mod_role(self, ctx, *, role_name: str):
        if not self.has_mod_role(ctx.author):
            return await ctx.send("No permission.")
        try:
            self.mod_roles.remove(role_name)
            await ctx.send(f"Removed '{role_name}' from mod roles.")
            await self.log_action(ctx, f"{ctx.author} removed '{role_name}' from mod roles.")
        except ValueError:
            await ctx.send("Role not found.")

    # -----------------------
    # Kick, Ban, Temp Ban
    # -----------------------
    @commands.command(name="kick")
    async def kick(self, ctx, member: nextcord.Member, *, reason=None):
        if not self.has_mod_role(ctx.author):
            return await ctx.send("No permission.")
        try:
            await member.kick(reason=reason)
            await ctx.send(f"{member} has been kicked.")
            await self.log_action(ctx, f"{ctx.author} kicked {member}. Reason: {reason}")
        except Exception as e:
            await ctx.send(f"Failed to kick: {e}")

    @commands.command(name="ban")
    async def ban(self, ctx, member: nextcord.Member, *, reason=None):
        if not self.has_mod_role(ctx.author):
            return await ctx.send("No permission.")
        try:
            await member.ban(reason=reason)
            await ctx.send(f"{member} has been banned.")
            await self.log_action(ctx, f"{ctx.author} banned {member}. Reason: {reason}")
        except Exception as e:
            await ctx.send(f"Failed to ban: {e}")

    @commands.command(name="tempban")
    async def temp_ban(self, ctx, member: nextcord.Member, duration: int, *, reason=None):
        if not self.has_mod_role(ctx.author):
            return await ctx.send("No permission.")
        try:
            await member.ban(reason=reason)
            unban_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=duration)
            self.temp_bans[member.id] = unban_time
            await ctx.send(f"{member} has been temp-banned for {duration}s.")
            await self.log_action(ctx, f"{ctx.author} temp-banned {member} for {duration}s. Reason: {reason}")
        except Exception as e:
            await ctx.send(f"Failed to temp-ban: {e}")

    # -----------------------
    # Mute / Unmute
    # -----------------------
    @commands.command(name="mute")
    async def mute(self, ctx, member: nextcord.Member, duration: int = 0):
        if not self.has_mod_role(ctx.author):
            return await ctx.send("No permission.")
        role = get(ctx.guild.roles, name="Muted")
        if not role:
            role = await ctx.guild.create_role(name="Muted", permissions=Permissions(send_messages=False))
            for channel in ctx.guild.channels:
                await channel.set_permissions(role, send_messages=False)
        await member.add_roles(role)
        await ctx.send(f"{member} has been muted.")
        await self.log_action(ctx, f"{ctx.author} muted {member}. Duration: {duration}s")
        if duration > 0:
            unmute_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=duration)
            self.temp_mutes[member.id] = (unmute_time, ctx.guild.id)

    @commands.command(name="unmute")
    async def unmute(self, ctx, member: nextcord.Member):
        if not self.has_mod_role(ctx.author):
            return await ctx.send("No permission.")
        role = get(ctx.guild.roles, name="Muted")
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send(f"{member} has been unmuted.")
            await self.log_action(ctx, f"{ctx.author} unmuted {member}.")
            if member.id in self.temp_mutes:
                del self.temp_mutes[member.id]
        else:
            await ctx.send(f"{member} is not muted.")

    # -----------------------
    # Purge
    # -----------------------
    @commands.command(name="purge")
    async def purge(self, ctx, amount: int):
        if not self.has_mod_role(ctx.author):
            return await ctx.send("No permission.")
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"Deleted {len(deleted)} messages.", delete_after=5)
        await self.log_action(ctx, f"{ctx.author} purged {len(deleted)} messages in {ctx.channel}.")

    # -----------------------
    # Background checks for temp bans/mutes
    # -----------------------
    @tasks.loop(seconds=10)
    async def check_temp_actions(self):
        # Temp bans
        for guild in self.bot.guilds:
            for user_id, unban_time in list(self.temp_bans.items()):
                if datetime.datetime.utcnow() >= unban_time:
                    try:
                        user = await self.bot.fetch_user(user_id)
                        await guild.unban(user)
                        await self.log_action(guild, f"{user} auto-unbanned after temp-ban.")
                        del self.temp_bans[user_id]
                    except:
                        continue

        # Temp mutes
        for user_id, (unmute_time, guild_id) in list(self.temp_mutes.items()):
            if datetime.datetime.utcnow() >= unmute_time:
                guild = self.bot.get_guild(guild_id)
                if guild:
                    member = guild.get_member(user_id)
                    if member:
                        role = get(guild.roles, name="Muted")
                        if role in member.roles:
                            await member.remove_roles(role)
                            await self.log_action(guild, f"{member} auto-unmuted after temp-mute.")
                    del self.temp_mutes[user_id]

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_temp_actions.start()


def setup(bot):
    bot.add_cog(Moderation(bot))
