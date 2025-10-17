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
    # Helpers
    # -----------------------
    def has_mod_role(self, member: nextcord.Member):
        return any(role.name in self.mod_roles for role in member.roles)

    async def log_action(self, ctx_or_interaction, message):
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

        # Check banned words
        for word in self.banned_words:
            if word.lower() in message.content.lower():
                await message.delete()
                await message.channel.send(f"{message.author.mention}, watch your language!", delete_after=5)
                await self.log_action(message, f"Deleted message with banned word from {message.author}")
                return

        # Check invites
        if self.invite_block and ("discord.gg/" in message.content.lower() or "discord.com/invite/" in message.content.lower()):
            await message.delete()
            await message.channel.send(f"{message.author.mention}, invites are not allowed!", delete_after=5)
            await self.log_action(message, f"Deleted invite from {message.author}")
            return

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
    # Banned words management
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

    @nextcord.slash_command(name="addword", description="Add a banned word")
    async def add_banned_word_slash(self, interaction: nextcord.Interaction, word: str):
        if not self.has_mod_role(interaction.user):
            return await interaction.response.send_message("No permission.", ephemeral=True)
        if word.lower() in self.banned_words:
            return await interaction.response.send_message("Word already banned.", ephemeral=True)
        self.banned_words.append(word.lower())
        await interaction.response.send_message(f"Added '{word}' to banned words.", ephemeral=True)
        await self.log_action(interaction, f"{interaction.user} added '{word}' to banned words.")

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

    @nextcord.slash_command(name="removeword", description="Remove a banned word")
    async def remove_banned_word_slash(self, interaction: nextcord.Interaction, word: str):
        if not self.has_mod_role(interaction.user):
            return await interaction.response.send_message("No permission.", ephemeral=True)
        try:
            self.banned_words.remove(word.lower())
            await interaction.response.send_message(f"Removed '{word}' from banned words.", ephemeral=True)
            await self.log_action(interaction, f"{interaction.user} removed '{word}' from banned words.")
        except ValueError:
            await interaction.response.send_message("Word not found in banned list.", ephemeral=True)

    # -----------------------
    # Mod roles management
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

    @nextcord.slash_command(name="addmodrole", description="Add a mod role")
    async def add_mod_role_slash(self, interaction: nextcord.Interaction, role_name: str):
        if not self.has_mod_role(interaction.user):
            return await interaction.response.send_message("No permission.", ephemeral=True)
        if role_name in self.mod_roles:
            return await interaction.response.send_message("Role already a mod role.", ephemeral=True)
        self.mod_roles.append(role_name)
        await interaction.response.send_message(f"Added '{role_name}' as a mod role.", ephemeral=True)
        await self.log_action(interaction, f"{interaction.user} added '{role_name}' to mod roles.")

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

    @nextcord.slash_command(name="removemodrole", description="Remove a mod role")
    async def remove_mod_role_slash(self, interaction: nextcord.Interaction, role_name: str):
        if not self.has_mod_role(interaction.user):
            return await interaction.response.send_message("No permission.", ephemeral=True)
        try:
            self.mod_roles.remove(role_name)
            await interaction.response.send_message(f"Removed '{role_name}' from mod roles.", ephemeral=True)
            await self.log_action(interaction, f"{interaction.user} removed '{role_name}' from mod roles.")
        except ValueError:
            await interaction.response.send_message("Role not found.", ephemeral=True)

    # -----------------------
    # Kick, Ban, Mute, Unmute
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
            await asyncio.sleep(duration)
            await member.remove_roles(role)
            await ctx.send(f"{member} has been unmuted.")
            await self.log_action(ctx, f"{member} auto-unmuted after {duration}s")

    @commands.command(name="unmute")
    async def unmute(self, ctx, member: nextcord.Member):
        if not self.has_mod_role(ctx.author):
            return await ctx.send("No permission.")
        role = get(ctx.guild.roles, name="Muted")
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send(f"{member} has been unmuted.")
            await self.log_action(ctx, f"{ctx.author} unmuted {member}.")
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

def setup(bot):
    bot.add_cog(Moderation(bot))
