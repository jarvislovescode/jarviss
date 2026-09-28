import feedparser
import discord
from discord import app_commands
from discord.ext import commands

from utils.embeds import jarvis_embed

FEEDS = {
    "world": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "tech": "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "business": "http://feeds.bbci.co.uk/news/business/rss.xml",
    "top": "http://feeds.bbci.co.uk/news/rss.xml",
}


class WorldNews(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="news", description="Get today's top headlines (free, no API key)")
    @app_commands.describe(category="Which category of news")
    @app_commands.choices(category=[
        app_commands.Choice(name="Top Stories", value="top"),
        app_commands.Choice(name="World", value="world"),
        app_commands.Choice(name="Technology", value="tech"),
        app_commands.Choice(name="Business", value="business"),
    ])
    async def news(self, interaction: discord.Interaction, category: app_commands.Choice[str] = None):
        cat_value = category.value if category else "top"
        await interaction.response.defer()

        feed = feedparser.parse(FEEDS[cat_value])
        entries = feed.entries[:6]

        if not entries:
            await interaction.followup.send("Couldn't reach the news wire just now, Sir. Try again shortly.")
            return

        lines = [f"**[{e.title}]({e.link})**" for e in entries]
        embed = jarvis_embed(
            f"Global Briefing — {category.name if category else 'Top Stories'}",
            "\n\n".join(lines),
        )
        embed.set_footer(text="Source: BBC News")
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(WorldNews(bot))
