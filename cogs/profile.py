import re

import discord
from discord import app_commands
from discord.ext import commands

from db import add_profile_entry, get_profile, clear_profile
from utils.embeds import jarvis_embed

# Lightweight, no-AI-call-needed pattern matching for passive preference learning.
# Deliberately simple and conservative — only fires on clear, explicit statements.
LIKE_PATTERNS = [
    re.compile(r"\bi (?:really )?(?:love|like|enjoy) ([a-zA-Z0-9 ,'\-]{3,40})", re.IGNORECASE),
    re.compile(r"\bmy favorite (?:is |food is |game is |movie is )?([a-zA-Z0-9 ,'\-]{3,40})", re.IGNORECASE),
]
DISLIKE_PATTERNS = [
    re.compile(r"\bi (?:really )?(?:hate|dislike|can'?t stand) ([a-zA-Z0-9 ,'\-]{3,40})", re.IGNORECASE),
]


def _clean(text: str) -> str:
    return text.strip().rstrip(".!,").strip()


class Profile(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        content = message.content
        if len(content) < 6:
            return

        for pattern in LIKE_PATTERNS:
            match = pattern.search(content)
            if match:
                add_profile_entry(message.author.id, "like", _clean(match.group(1)))
                break

        for pattern in DISLIKE_PATTERNS:
            match = pattern.search(content)
            if match:
                add_profile_entry(message.author.id, "dislike", _clean(match.group(1)))
                break

    @app_commands.command(name="profile", description="See what J.A.R.V.I.S has learned about you")
    async def profile(self, interaction: discord.Interaction):
        data = get_profile(interaction.user.id)
        if not any(data.values()):
            await interaction.response.send_message(
                "I have no dossier on you yet, Sir. Talk to me more — I'm always listening. "
                "Well, reading, technically.",
                ephemeral=True,
            )
            return
        embed = jarvis_embed(f"Dossier: {interaction.user.display_name}")
        if data["likes"]:
            embed.add_field(name="Likes", value="\n".join(f"• {x}" for x in data["likes"][:10]), inline=False)
        if data["dislikes"]:
            embed.add_field(name="Dislikes", value="\n".join(f"• {x}" for x in data["dislikes"][:10]), inline=False)
        if data["notes"]:
            embed.add_field(name="Notes", value="\n".join(f"• {x}" for x in data["notes"][:10]), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="profile_add", description="Manually tell J.A.R.V.I.S something about yourself")
    @app_commands.describe(kind="like, dislike, or note", content="What should I remember?")
    @app_commands.choices(kind=[
        app_commands.Choice(name="like", value="like"),
        app_commands.Choice(name="dislike", value="dislike"),
        app_commands.Choice(name="note", value="note"),
    ])
    async def profile_add(self, interaction: discord.Interaction, kind: app_commands.Choice[str], content: str):
        add_profile_entry(interaction.user.id, kind.value, content)
        await interaction.response.send_message("Filed, Sir. I'll factor that in going forward.", ephemeral=True)

    @app_commands.command(name="profile_forget", description="Wipe everything J.A.R.V.I.S has learned about you")
    async def profile_forget(self, interaction: discord.Interaction):
        clear_profile(interaction.user.id)
        await interaction.response.send_message("Dossier cleared. A clean slate, Sir.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Profile(bot))
