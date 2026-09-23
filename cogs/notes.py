import discord
from discord import app_commands
from discord.ext import commands

from db import add_note, get_notes


class Notes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="note", description="Save a quick note for J.A.R.V.I.S to remember")
    @app_commands.describe(content="What should I remember?")
    async def note(self, interaction: discord.Interaction, content: str):
        add_note(interaction.user.id, content)
        await interaction.response.send_message("Filed away, Sir.")

    @app_commands.command(name="notes", description="See your saved notes")
    async def notes(self, interaction: discord.Interaction):
        rows = get_notes(interaction.user.id)
        if not rows:
            await interaction.response.send_message("No notes on file, Sir.", ephemeral=True)
            return
        listing = "\n".join(f"• {r['content']}" for r in rows)
        await interaction.response.send_message(f"Your notes, Sir:\n{listing}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Notes(bot))
