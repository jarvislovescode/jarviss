import discord
from discord import app_commands
from discord.ext import commands
from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL, OWNER_ID, RHODEY_ID
from persona import SYSTEM_PROMPT

groq_client = Groq(api_key=GROQ_API_KEY)


class AIChat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _context_note(self, user_id: int) -> str:
        if user_id == OWNER_ID:
            return "[The person speaking to you right now IS the server owner, Sir.]"
        if user_id == RHODEY_ID:
            return "[The person speaking to you right now IS Rhodey, the owner's best friend.]"
        return "[The person speaking to you is a regular member, not the owner or Rhodey.]"

    async def ask_ai(self, user_id: int, prompt: str) -> str:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": self._context_note(user_id)},
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
            temperature=0.8,
        )
        return completion.choices[0].message.content

    @app_commands.command(name="ask", description="Ask J.A.R.V.I.S anything")
    @app_commands.describe(prompt="What do you want to ask?")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        try:
            reply = await self.ask_ai(interaction.user.id, prompt)
        except Exception as e:
            reply = f"Apologies, Sir — I've hit a snag: `{e}`"
        await interaction.followup.send(reply)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if self.bot.user in message.mentions:
            prompt = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
            if not prompt:
                prompt = "Say hello and introduce yourself briefly."
            async with message.channel.typing():
                try:
                    reply = await self.ask_ai(message.author.id, prompt)
                except Exception as e:
                    reply = f"Apologies, Sir — I've hit a snag: `{e}`"
            await message.reply(reply, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(AIChat(bot))
