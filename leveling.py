import time

import discord
from discord import app_commands
from discord.ext import commands

from db import add_xp, get_xp, get_leaderboard
from utils.embeds import jarvis_embed, GOLD

XP_PER_MESSAGE = 10
COOLDOWN_SECONDS = 60  # per user, prevents XP farming by spamming


class Leveling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._last_xp: dict[int, float] = {}  # user_id -> timestamp

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        now = time.time()
        last = self._last_xp.get(message.author.id, 0)
        if now - last < COOLDOWN_SECONDS:
            return
        self._last_xp[message.author.id] = now

        new_xp, new_level, leveled_up = add_xp(message.author.id, XP_PER_MESSAGE)
        if leveled_up:
            embed = jarvis_embed(
                "Clearance Upgraded",
                f"{message.author.mention} has been promoted to **Level {new_level}**. "
                f"Try not to let it go to your head.",
                color=GOLD,
            )
            try:
                await message.channel.send(embed=embed)
            except discord.HTTPException:
                pass

    @app_commands.command(name="rank", description="Check your (or someone else's) J.A.R.V.I.S clearance level")
    @app_commands.describe(user="Whose rank to check (defaults to you)")
    async def rank(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        data = get_xp(target.id)
        progress = data["xp"] % 100
        embed = jarvis_embed(
            f"{target.display_name}'s Clearance File",
            f"**Level:** {data['level']}\n"
            f"**XP:** {data['xp']}\n"
            f"**Progress to next level:** {progress}/100",
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="See the top-ranked members in this server")
    async def leaderboard(self, interaction: discord.Interaction):
        rows = get_leaderboard(10)
        if not rows:
            await interaction.response.send_message("No data yet, Sir. Rather quiet around here.")
            return
        lines = []
        for i, r in enumerate(rows, start=1):
            lines.append(f"**{i}.** <@{r['user_id']}> — Level {r['level']} ({r['xp']} XP)")
        embed = jarvis_embed("Server Leaderboard", "\n".join(lines))
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))
