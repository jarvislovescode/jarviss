import discord
from discord import app_commands
from discord.ext import commands
from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL, OWNER_ID, RHODEY_ID
from persona import ROAST_SYSTEM_PROMPT

groq_client = Groq(api_key=GROQ_API_KEY)


class Roast(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="roast", description="J.A.R.V.I.S roasts someone (playfully)")
    @app_commands.describe(target="Who should be roasted?")
    async def roast(self, interaction: discord.Interaction, target: discord.Member):
        if target.id == OWNER_ID:
            await interaction.response.send_message(
                "I'm afraid I must decline, Sir — I won't roast you. "
                "My loyalty has limits, and that's one of them."
            )
            return
        if target.id == RHODEY_ID:
            await interaction.response.send_message(
                "Rhodey is off-limits. I have too much respect for him to try."
            )
            return
        if target.bot:
            await interaction.response.send_message(
                "I'll refrain from roasting a fellow machine. Professional courtesy."
            )
            return

        await interaction.response.defer()
        try:
            completion = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": ROAST_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Roast {target.display_name}."},
                ],
                max_tokens=150,
                temperature=0.9,
            )
            reply = completion.choices[0].message.content
        except Exception as e:
            reply = f"My roast circuits misfired, Sir: `{e}`"

        await interaction.followup.send(f"{target.mention}\n{reply}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Roast(bot))
