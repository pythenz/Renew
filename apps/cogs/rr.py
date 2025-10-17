import nextcord
from nextcord.ext import commands
from nextcord import Interaction, Embed
from nextcord.utils import get
import json
import os

class ReactionRoleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.file_path = "reaction_roles.json"
        self.reaction_roles = self.load_data()

    # -----------------------
    # Persistence helpers
    # -----------------------
    def save_data(self):
        with open(self.file_path, "w") as f:
            json.dump(self.reaction_roles, f)

    def load_data(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                return json.load(f)
        return {}

    # -----------------------
    # Create reaction role (prefix)
    # -----------------------
    @commands.command(name="create_rr")
    async def create_reaction_role(self, ctx, *, roles_and_emojis: str):
        try:
            mappings = {}
            description_lines = []

            for pair in roles_and_emojis.split(","):
                emoji, role_name = pair.split(":")
                emoji = emoji.strip()
                role_name = role_name.strip()
                role = get(ctx.guild.roles, name=role_name)
                if not role:
                    await ctx.send(f"Role '{role_name}' not found.")
                    return
                mappings[emoji] = role_name
                description_lines.append(f"{emoji} → {role_name}")

            embed = Embed(title="Reaction Roles", description="\n".join(description_lines))
            message = await ctx.send(embed=embed)

            for emoji in mappings:
                await message.add_reaction(emoji)

            self.reaction_roles[str(message.id)] = mappings
            self.save_data()
            await ctx.send("Reaction role message created successfully!")

        except Exception as e:
            await ctx.send(f"Error creating reaction role: {e}")

    # -----------------------
    # Create reaction role (slash)
    # -----------------------
    @nextcord.slash_command(name="create_rr", description="Create a multi-reaction-role embed")
    async def create_reaction_role_slash(self, interaction: Interaction, roles_and_emojis: str):
        try:
            mappings = {}
            description_lines = []
            guild = interaction.guild

            for pair in roles_and_emojis.split(","):
                emoji, role_name = pair.split(":")
                emoji = emoji.strip()
                role_name = role_name.strip()
                role = get(guild.roles, name=role_name)
                if not role:
                    return await interaction.response.send_message(f"Role '{role_name}' not found.", ephemeral=True)
                mappings[emoji] = role_name
                description_lines.append(f"{emoji} → {role_name}")

            embed = Embed(title="Reaction Roles", description="\n".join(description_lines))
            message = await interaction.channel.send(embed=embed)

            for emoji in mappings:
                await message.add_reaction(emoji)

            self.reaction_roles[str(message.id)] = mappings
            self.save_data()
            await interaction.response.send_message("Reaction role message created successfully!", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"Error creating reaction role: {e}", ephemeral=True)

    # -----------------------
    # Delete reaction role (prefix)
    # -----------------------
    @commands.command(name="delete_rr")
    async def delete_reaction_role(self, ctx, message_id: int):
        if str(message_id) in self.reaction_roles:
            try:
                msg = await ctx.channel.fetch_message(message_id)
                await msg.delete()
            except Exception:
                pass  # message may already be deleted
            del self.reaction_roles[str(message_id)]
            self.save_data()
            await ctx.send(f"Deleted reaction role message `{message_id}` and removed from tracking.")
        else:
            await ctx.send("Message ID not found in reaction role list.")

    # -----------------------
    # Delete reaction role (slash)
    # -----------------------
    @nextcord.slash_command(name="delete_rr", description="Delete a reaction-role message")
    async def delete_reaction_role_slash(self, interaction: Interaction, message_id: int):
        if str(message_id) in self.reaction_roles:
            try:
                msg = await interaction.channel.fetch_message(message_id)
                await msg.delete()
            except Exception:
                pass
            del self.reaction_roles[str(message_id)]
            self.save_data()
            await interaction.response.send_message(f"Deleted reaction role message `{message_id}` and removed from tracking.", ephemeral=True)
        else:
            await interaction.response.send_message("Message ID not found in reaction role list.", ephemeral=True)

    # -----------------------
    # Listeners for role add/remove
    # -----------------------
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        if str(payload.message_id) in self.reaction_roles:
            emoji_to_role = self.reaction_roles[str(payload.message_id)]
            emoji_str = str(payload.emoji)
            if emoji_str in emoji_to_role:
                guild = self.bot.get_guild(payload.guild_id)
                role = get(guild.roles, name=emoji_to_role[emoji_str])
                member = guild.get_member(payload.user_id)
                if role and member:
                    await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        if str(payload.message_id) in self.reaction_roles:
            emoji_to_role = self.reaction_roles[str(payload.message_id)]
            emoji_str = str(payload.emoji)
            if emoji_str in emoji_to_role:
                guild = self.bot.get_guild(payload.guild_id)
                role = get(guild.roles, name=emoji_to_role[emoji_str])
                member = guild.get_member(payload.user_id)
                if role and member:
                    await member.remove_roles(role)

def setup(bot):
    bot.add_cog(ReactionRoleCog(bot))
