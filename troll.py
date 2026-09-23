import random
import time

import discord
from discord.ext import commands
from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL, OWNER_ID, RHODEY_ID
from persona import TROLL_SYSTEM_PROMPT, TROLL_FLAVOR_LINES
from db import get_guild_settings

groq_client = Groq(api_key=GROQ_API_KEY)

# Per-channel cooldown so JARVIS doesn't troll every message in a busy channel
COOLDOWN_SECONDS = 120
MIN_MESSAGE_LENGTH = 8  # don't troll one-word/emoji-only messages


class Troll(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._last_troll: dict[int, float] = {}  # channel_id -> timestamp

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if self.bot.user in message.mentions:
            return  # let ai_chat.py handle direct mentions, don't double-fire
        if len(message.content) < MIN_MESSAGE_LENGTH:
            return
        if message.author.id in (OWNER_ID, RHODEY_ID):
            return  # never unprompted-troll the owner or Rhodey

        settings = get_guild_settings(message.guild.id)
        if not settings.get("troll_enabled", 1):
            return

        now = time.time()
        last = self._last_troll.get(message.channel.id, 0)
        if now - last < COOLDOWN_SECONDS:
            return

        chance = settings.get("troll_chance", 4)  # percent
        if random.randint(1, 100) > chance:
            return

        self._last_troll[message.channel.id] = now

        try:
            completion = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": TROLL_SYSTEM_PROMPT},
                    {"role": "user", "content": message.content},
                ],
                max_tokens=100,
                temperature=1.0,
            )
            reply = completion.choices[0].message.content.strip()
            if reply.upper() == "SKIP" or not reply:
                return
        except Exception:
            reply = random.choice(TROLL_FLAVOR_LINES)

        try:
            await message.reply(reply, mention_author=False)
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Troll(bot))
