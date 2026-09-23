import re
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import add_reminder, get_due_reminders, delete_reminder

DURATION_RE = re.compile(r"(\d+)\s*(s|sec|m|min|h|hr|hour|d|day)s?", re.IGNORECASE)

UNIT_SECONDS = {
    "s": 1, "sec": 1,
    "m": 60, "min": 60,
    "h": 3600, "hr": 3600, "hour": 3600,
    "d": 86400, "day": 86400,
}


def parse_duration(text: str) -> int | None:
    """Parses things like '10m', '2h', '1d' into seconds."""
    match = DURATION_RE.match(text.strip())
    if not match:
        return None
    amount, unit = match.groups()
    return int(amount) * UNIT_SECONDS[unit.lower()]


class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()

    async def cog_load(self):
        self.scheduler.add_job(self.check_reminders, "interval", seconds=30)
        self.scheduler.start()

    async def check_reminders(self):
        now_iso = datetime.now(timezone.utc).isoformat()
        for reminder in get_due_reminders(now_iso):
            channel = self.bot.get_channel(reminder["channel_id"])
            if channel:
                try:
                    await channel.send(
                        f"<@{reminder['user_id']}> Reminder, Sir: {reminder['message']}"
                    )
                except discord.HTTPException:
                    pass
            delete_reminder(reminder["id"])

    @app_commands.command(name="remind", description="Set a reminder (e.g. 10m, 2h, 1d)")
    @app_commands.describe(when="Duration like 10m, 2h, 1d", message="What to remind you about")
    async def remind(self, interaction: discord.Interaction, when: str, message: str):
        seconds = parse_duration(when)
        if seconds is None:
            await interaction.response.send_message(
                "I couldn't parse that duration, Sir. Try formats like `10m`, `2h`, or `1d`.",
                ephemeral=True,
            )
            return

        remind_at = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        add_reminder(
            interaction.user.id,
            interaction.channel_id,
            message,
            remind_at.isoformat(),
        )
        await interaction.response.send_message(
            f"Noted, Sir. I'll remind you about \"{message}\" in {when}."
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))
