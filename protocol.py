import discord
from discord import app_commands
from discord.ext import commands

from utils.embeds import jarvis_embed, RED, GOLD


def is_mod():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.manage_messages
    return app_commands.check(predicate)


class Protocol(commands.Cog):
    """Iron-Man-suit-themed moderation commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="protocol_lockdown", description="Slow this channel down (admin only)")
    @app_commands.describe(seconds="Slowmode delay in seconds (0 to disable)")
    @is_mod()
    async def protocol_lockdown(self, interaction: discord.Interaction, seconds: app_commands.Range[int, 0, 21600]):
        await interaction.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            embed = jarvis_embed("Protocol: Lockdown Lifted", "Channel restored to normal speed, Sir.", color=GOLD)
        else:
            embed = jarvis_embed(
                "Protocol: Lockdown Engaged",
                f"Slowmode set to {seconds}s. Everyone, take a breath.",
                color=RED,
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="protocol_clean", description="Bulk-delete recent messages (admin only)")
    @app_commands.describe(amount="How many recent messages to delete (max 100)")
    @is_mod()
    async def protocol_clean(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100]):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        embed = jarvis_embed(
            "Protocol: Clean Sweep",
            f"Disposed of {len(deleted)} message(s). Tidy as ever.",
            color=GOLD,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @protocol_lockdown.error
    @protocol_clean.error
    async def on_mod_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                "You lack the clearance for that protocol, Sir would need to authorize it.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(f"Protocol failed: `{error}`", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Protocol(bot))
