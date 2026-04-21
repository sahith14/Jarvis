import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "jarvis_memory.db"

def get_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS preferences (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS command_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT,
            response TEXT,
            timestamp TEXT
        );
        CREATE TABLE IF NOT EXISTS learned_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact TEXT,
            source TEXT,
            created_at TEXT
        );
    """)
    conn.commit()
    conn.close()

init_db()

def set_preference(key: str, value: str):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO preferences (key, value, updated_at) VALUES (?, ?, ?)",
        (key, value, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_preference(key: str, default=None):
    conn = get_db()
    row = conn.execute("SELECT value FROM preferences WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default

def log_command(command: str, response: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO command_history (command, response, timestamp) VALUES (?, ?, ?)",
        (command, response, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_recent_commands(limit: int = 10):
    conn = get_db()
    rows = conn.execute(
        "SELECT command, response, timestamp FROM command_history ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_fact(fact: str, source: str = "conversation"):
    conn = get_db()
    conn.execute(
        "INSERT INTO learned_facts (fact, source, created_at) VALUES (?, ?, ?)",
        (fact, source, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def search_facts(query: str, limit: int = 5):
    conn = get_db()
    rows = conn.execute(
        "SELECT fact FROM learned_facts WHERE fact LIKE ? ORDER BY id DESC LIMIT ?",
        (f"%{query}%", limit)
    ).fetchall()
    conn.close()
    return [r["fact"] for r in rows]

def build_memory_context(user_input: str) -> str:
    """Build context string from memory for LLM."""
    parts = []
    # User name preference
    name = get_preference("user_name", "sir")
    parts.append(f"User prefers to be called: {name}")
    # Recent commands context
    recent = get_recent_commands(3)
    if recent:
        parts.append("Recent interactions:")
        for r in recent:
            parts.append(f"- User: {r['command']} | JARVIS: {r['response'][:50]}")
    # Relevant facts
    facts = search_facts(user_input, 3)
    if facts:
        parts.append("Remembered facts:")
        for f in facts:
            parts.append(f"- {f}")
    return "\n".join(parts)
