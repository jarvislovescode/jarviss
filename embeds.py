import discord

GOLD = discord.Color.gold()
RED = discord.Color.from_rgb(200, 30, 30)
BLUE = discord.Color.from_rgb(40, 120, 220)


def jarvis_embed(title: str, description: str = "", color=GOLD) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="J.A.R.V.I.S")
    return embed
