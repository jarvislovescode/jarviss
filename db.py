import sqlite3
from contextlib import contextmanager

from config import DB_PATH


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                remind_at TEXT NOT NULL
            )
        """)
        # Conversation memory — per channel, so JARVIS can recall recent chat
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                display_name TEXT,
                role TEXT NOT NULL,        -- 'user' or 'assistant'
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Per-guild customization (mood, troll toggle/frequency)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                mood TEXT DEFAULT 'sarcastic',
                troll_enabled INTEGER DEFAULT 1,
                troll_chance INTEGER DEFAULT 4  -- percent, 0-100
            )
        """)
        # Per-user customization (nickname JARVIS uses for them)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                nickname TEXT
            )
        """)
        # XP / leveling
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_xp (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )
        """)
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ---------- Notes ----------

def add_note(user_id: int, content: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO notes (user_id, content) VALUES (?, ?)",
            (user_id, content),
        )
        conn.commit()


def get_notes(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT content, created_at FROM notes WHERE user_id = ? ORDER BY id DESC LIMIT 10",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- Reminders ----------

def add_reminder(user_id: int, channel_id: int, message: str, remind_at: str):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO reminders (user_id, channel_id, message, remind_at) VALUES (?, ?, ?, ?)",
            (user_id, channel_id, message, remind_at),
        )
        conn.commit()
        return cur.lastrowid


def get_due_reminders(now_iso: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM reminders WHERE remind_at <= ?",
            (now_iso,),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_reminder(reminder_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        conn.commit()


# ---------- Conversation memory ----------

def add_message(channel_id: int, user_id: int, display_name: str, role: str, content: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO conversations (channel_id, user_id, display_name, role, content) "
            "VALUES (?, ?, ?, ?, ?)",
            (channel_id, user_id, display_name, role, content),
        )
        conn.commit()
        # Keep only the most recent 40 messages per channel to stay lean
        conn.execute("""
            DELETE FROM conversations
            WHERE channel_id = ? AND id NOT IN (
                SELECT id FROM conversations
                WHERE channel_id = ?
                ORDER BY id DESC LIMIT 40
            )
        """, (channel_id, channel_id))
        conn.commit()


def get_recent_messages(channel_id: int, limit: int = 12):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT display_name, role, content FROM conversations "
            "WHERE channel_id = ? ORDER BY id DESC LIMIT ?",
            (channel_id, limit),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]


def clear_channel_memory(channel_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM conversations WHERE channel_id = ?", (channel_id,))
        conn.commit()


# ---------- Guild settings (mood / troll) ----------

def get_guild_settings(guild_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)
        ).fetchone()
        if row:
            return dict(row)
        conn.execute("INSERT INTO guild_settings (guild_id) VALUES (?)", (guild_id,))
        conn.commit()
        return {"guild_id": guild_id, "mood": "sarcastic", "troll_enabled": 1, "troll_chance": 4}


def set_guild_mood(guild_id: int, mood: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO guild_settings (guild_id, mood) VALUES (?, ?) "
            "ON CONFLICT(guild_id) DO UPDATE SET mood = excluded.mood",
            (guild_id, mood),
        )
        conn.commit()


def set_guild_troll(guild_id: int, enabled: bool = None, chance: int = None):
    settings = get_guild_settings(guild_id)
    new_enabled = int(enabled) if enabled is not None else settings["troll_enabled"]
    new_chance = chance if chance is not None else settings["troll_chance"]
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO guild_settings (guild_id, troll_enabled, troll_chance) VALUES (?, ?, ?) "
            "ON CONFLICT(guild_id) DO UPDATE SET "
            "troll_enabled = excluded.troll_enabled, troll_chance = excluded.troll_chance",
            (guild_id, new_enabled, new_chance),
        )
        conn.commit()


# ---------- User settings (nickname) ----------

def get_user_nickname(user_id: int) -> str | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT nickname FROM user_settings WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row["nickname"] if row else None


def set_user_nickname(user_id: int, nickname: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO user_settings (user_id, nickname) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET nickname = excluded.nickname",
            (user_id, nickname),
        )
        conn.commit()


# ---------- XP / Leveling ----------

def _level_for_xp(xp: int) -> int:
    return xp // 100 + 1


def add_xp(user_id: int, amount: int = 10):
    """Adds XP, returns (new_xp, new_level, leveled_up: bool)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT xp, level FROM user_xp WHERE user_id = ?", (user_id,)
        ).fetchone()
        old_level = row["level"] if row else 1
        old_xp = row["xp"] if row else 0
        new_xp = old_xp + amount
        new_level = _level_for_xp(new_xp)
        conn.execute(
            "INSERT INTO user_xp (user_id, xp, level) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET xp = excluded.xp, level = excluded.level",
            (user_id, new_xp, new_level),
        )
        conn.commit()
        return new_xp, new_level, new_level > old_level


def get_xp(user_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT xp, level FROM user_xp WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else {"xp": 0, "level": 1}


def get_leaderboard(limit: int = 10):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT user_id, xp, level FROM user_xp ORDER BY xp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
