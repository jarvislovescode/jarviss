import discord
from discord import app_commands
from discord.ext import commands

from db import set_guild_troll, get_guild_settings


def is_admin():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.manage_guild
    return app_commands.check(predicate)


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="troll_toggle", description="Turn J.A.R.V.I.S's random trolling on/off (admin only)")
    @is_admin()
    async def troll_toggle(self, interaction: discord.Interaction, enabled: bool):
        set_guild_troll(interaction.guild_id, enabled=enabled)
        msg = "Troll mode engaged. Brace yourselves." if enabled else "Troll mode disengaged. Boring, but fine."
        await interaction.response.send_message(msg)

    @app_commands.command(name="troll_chance", description="Set how often (%) J.A.R.V.I.S randomly trolls messages (admin only)")
    @app_commands.describe(percent="0-100, chance per eligible message")
    @is_admin()
    async def troll_chance(self, interaction: discord.Interaction, percent: app_commands.Range[int, 0, 100]):
        set_guild_troll(interaction.guild_id, chance=percent)
        await interaction.response.send_message(f"Troll frequency set to {percent}%. Adjust wisely.")

    @app_commands.command(name="jarvis_status", description="See J.A.R.V.I.S's current settings for this server")
    async def jarvis_status(self, interaction: discord.Interaction):
        s = get_guild_settings(interaction.guild_id)
        embed = discord.Embed(title="J.A.R.V.I.S — System Status", color=discord.Color.gold())
        embed.add_field(name="Mood", value=s.get("mood", "sarcastic").capitalize(), inline=True)
        embed.add_field(name="Troll Mode", value="On" if s.get("troll_enabled") else "Off", inline=True)
        embed.add_field(name="Troll Chance", value=f"{s.get('troll_chance', 4)}%", inline=True)
        await interaction.response.send_message(embed=embed)

    @troll_toggle.error
    @troll_chance.error
    async def on_admin_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                "Nice try. You'll need 'Manage Server' permissions to touch that, Sir's not going to like this.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(f"Something broke: `{error}`", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Settings(bot))
