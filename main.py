import asyncio
import logging

import discord
from discord.ext import commands

from config import DISCORD_TOKEN, OWNER_ID
from db import init_db
from keep_alive import keep_alive

logging.basicConfig(level=logging.INFO)

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

COGS = [
    "cogs.ai_chat",
    "cogs.roast",
    "cogs.reminders",
    "cogs.notes",
]


@bot.event
async def on_ready():
    print(f"J.A.R.V.I.S online as {bot.user}. At your service.")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Slash command sync failed: {e}")

    if OWNER_ID:
        try:
            owner = await bot.fetch_user(OWNER_ID)
            await owner.send("Systems online, Sir. J.A.R.V.I.S at your service.")
        except discord.HTTPException:
            pass


async def main():
    init_db()
    keep_alive()
    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
