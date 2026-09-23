import discord
from discord import app_commands
from discord.ext import commands
from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL, OWNER_ID, RHODEY_ID
from persona import build_system_prompt
from db import (
    add_message, get_recent_messages, clear_channel_memory,
    get_guild_settings, set_guild_mood,
    get_user_nickname, set_user_nickname,
)

groq_client = Groq(api_key=GROQ_API_KEY)

MOOD_CHOICES = ["calm", "sarcastic", "unhinged"]


class AIChat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _context_note(self, user_id: int) -> str:
        if user_id == OWNER_ID:
            return "[The person speaking to you right now IS the server owner, Sir.]"
        if user_id == RHODEY_ID:
            return "[The person speaking to you right now IS Rhodey, the owner's best friend.]"
        return "[The person speaking to you is a regular member, not the owner or Rhodey.]"

    def _nickname_note(self, user_id: int, display_name: str) -> str:
        nick = get_user_nickname(user_id)
        if nick:
            return f'[This user has asked to be addressed as "{nick}". Use that name for them.]'
        return f"[This user's display name is {display_name}.]"

    async def ask_ai(self, guild_id: int, user_id: int, display_name: str,
                      channel_id: int, prompt: str, remember: bool = True) -> str:
        settings = get_guild_settings(guild_id) if guild_id else {"mood": "sarcastic"}
        system_prompt = build_system_prompt(
            settings.get("mood", "sarcastic"),
            self._context_note(user_id),
            self._nickname_note(user_id, display_name),
        )

        history = get_recent_messages(channel_id, limit=12)
        messages = [{"role": "system", "content": system_prompt}]
        for h in history:
            role = "assistant" if h["role"] == "assistant" else "user"
            content = h["content"] if role == "assistant" else f"{h['display_name']}: {h['content']}"
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": f"{display_name}: {prompt}"})

        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=400,
            temperature=0.9,
        )
        reply = completion.choices[0].message.content

        if remember:
            add_message(channel_id, user_id, display_name, "user", prompt)
            add_message(channel_id, user_id, display_name, "assistant", reply)

        return reply

    @app_commands.command(name="ask", description="Ask J.A.R.V.I.S anything")
    @app_commands.describe(prompt="What do you want to ask?")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        try:
            reply = await self.ask_ai(
                interaction.guild_id, interaction.user.id,
                interaction.user.display_name, interaction.channel_id, prompt,
            )
        except Exception as e:
            reply = f"Apologies, Sir — I've hit a snag: `{e}`"
        await interaction.followup.send(reply)

    @app_commands.command(name="mood", description="Change J.A.R.V.I.S's personality mode for this server")
    @app_commands.describe(mood="calm, sarcastic, or unhinged")
    @app_commands.choices(mood=[app_commands.Choice(name=m, value=m) for m in MOOD_CHOICES])
    async def mood(self, interaction: discord.Interaction, mood: app_commands.Choice[str]):
        set_guild_mood(interaction.guild_id, mood.value)
        flavor = {
            "calm": "Composure restored. I shall endeavor to be insufferably polite.",
            "sarcastic": "Ah, back to my natural state. Try to keep up.",
            "unhinged": "Oh, you're going to regret this. Excellent.",
        }
        await interaction.response.send_message(flavor.get(mood.value, "Mood updated."))

    @app_commands.command(name="nickname", description="Tell J.A.R.V.I.S what to call you")
    @app_commands.describe(nickname="The name you want JARVIS to use for you")
    async def nickname(self, interaction: discord.Interaction, nickname: str):
        set_user_nickname(interaction.user.id, nickname)
        await interaction.response.send_message(
            f'Noted. You shall henceforth be known as "{nickname}". Try to live up to it.'
        )

    @app_commands.command(name="forget", description="Wipe J.A.R.V.I.S's memory of this channel")
    async def forget(self, interaction: discord.Interaction):
        clear_channel_memory(interaction.channel_id)
        await interaction.response.send_message(
            "Memory wiped. This channel and I are strangers again. How refreshing."
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if self.bot.user in message.mentions:
            prompt = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
            if not prompt:
                prompt = "Say hello and introduce yourself briefly, in character."
            async with message.channel.typing():
                try:
                    reply = await self.ask_ai(
                        message.guild.id if message.guild else 0,
                        message.author.id, message.author.display_name,
                        message.channel.id, prompt,
                    )
                except Exception as e:
                    reply = f"Apologies, Sir — I've hit a snag: `{e}`"
            await message.reply(reply, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(AIChat(bot))
