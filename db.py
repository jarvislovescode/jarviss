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
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


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
