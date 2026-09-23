import urllib.parse

import discord
from discord import app_commands
from discord.ext import commands

from utils.embeds import jarvis_embed

# Pollinations.ai — free, no API key required
IMAGE_BASE_URL = "https://image.pollinations.ai/prompt/"


class Imagine(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="imagine", description="Generate an AI image from a prompt")
    @app_commands.describe(prompt="Describe what you want to see")
    async def imagine(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        encoded = urllib.parse.quote(prompt)
        image_url = f"{IMAGE_BASE_URL}{encoded}?width=1024&height=1024&nologo=true"
        embed = jarvis_embed(
            "Rendering Complete",
            f'"{prompt}"',
        )
        embed.set_image(url=image_url)
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Imagine(bot))
