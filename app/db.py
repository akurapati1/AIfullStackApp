"""Tiny SQLite persistence layer for conversations and messages."""
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, id);
"""


class Database:
    def __init__(self, path: str):
        self.path = path
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._memory_conn = sqlite3.connect(":memory:", check_same_thread=False) if path == ":memory:" else None
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = self._memory_conn or sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if self._memory_conn is None:
                conn.close()

    def create_conversation(self, title: str) -> dict:
        cid = uuid.uuid4().hex
        with self.connect() as conn:
            conn.execute("INSERT INTO conversations (id, title) VALUES (?, ?)", (cid, title[:80]))
            row = conn.execute("SELECT * FROM conversations WHERE id = ?", (cid,)).fetchone()
        return dict(row)

    def list_conversations(self) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM conversations ORDER BY created_at DESC, rowid DESC").fetchall()
        return [dict(r) for r in rows]

    def get_conversation(self, cid: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM conversations WHERE id = ?", (cid,)).fetchone()
        return dict(row) if row else None

    def delete_conversation(self, cid: str) -> bool:
        with self.connect() as conn:
            cur = conn.execute("DELETE FROM conversations WHERE id = ?", (cid,))
        return cur.rowcount > 0

    def add_message(self, cid: str, role: str, content: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
                (cid, role, content),
            )

    def get_messages(self, cid: str, limit: int | None = None) -> list[dict]:
        with self.connect() as conn:
            if limit:
                rows = conn.execute(
                    "SELECT role, content, created_at FROM (SELECT * FROM messages WHERE conversation_id = ? "
                    "ORDER BY id DESC LIMIT ?) ORDER BY id ASC",
                    (cid, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY id ASC",
                    (cid,),
                ).fetchall()
        return [dict(r) for r in rows]
