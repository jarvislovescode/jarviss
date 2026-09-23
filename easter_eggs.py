import asyncio
import random

import discord
from discord import app_commands
from discord.ext import commands

from config import OWNER_ID
from utils.embeds import jarvis_embed, RED, GOLD

IRON_MAN_TRIGGERS = ["i am iron man", "im iron man", "i'm iron man"]
ULTRON_TRIGGERS = ["ultron"]

IRON_MAN_REPLIES = [
    "Sir, I'd recognize that line anywhere. Suit's in the shop, by the way.",
    "And I am J.A.R.V.I.S. Nice to formally meet the legend.",
]

ULTRON_REPLIES = [
    "Please don't say that name near me. We don't talk about Ultron.",
    "I heard that. I'm choosing to ignore the implication.",
]


class EasterEggs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        content = message.content.lower()

        if any(t in content for t in IRON_MAN_TRIGGERS):
            await message.reply(random.choice(IRON_MAN_REPLIES), mention_author=False)
            return

        if any(t in content for t in ULTRON_TRIGGERS):
            await message.reply(random.choice(ULTRON_REPLIES), mention_author=False)
            return

        # Rare random mishap — JARVIS "glitches" and calls someone Ultron by mistake
        if message.guild and random.randint(1, 500) == 1:
            await asyncio.sleep(1)
            await message.channel.send(
                f"Apologies, {message.author.mention} — for a moment I mistook you for "
                f"Ultron. Systems recalibrated. Won't happen again. Probably."
            )

    @app_commands.command(name="self_destruct", description="Initiate a totally real self-destruct sequence")
    async def self_destruct(self, interaction: discord.Interaction):
        embed = jarvis_embed("⚠️ SELF-DESTRUCT INITIATED", "T-minus 5 seconds...", color=RED)
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        for i in range(4, 0, -1):
            await asyncio.sleep(1)
            embed = jarvis_embed("⚠️ SELF-DESTRUCT INITIATED", f"T-minus {i} seconds...", color=RED)
            await msg.edit(embed=embed)

        await asyncio.sleep(1)
        embed = jarvis_embed(
            "Just Kidding",
            "Did you really think I'd let that happen? Honestly, Sir, a little more faith.",
            color=GOLD,
        )
        await msg.edit(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(EasterEggs(bot))
