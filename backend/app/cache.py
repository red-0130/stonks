import sqlite3
import json
import time
import os
from typing import Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "cache.sqlite3")

def init_cache():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cache_entries (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            expires_at REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_cached(key: str) -> Optional[Any]:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = time.time()
        cursor.execute("SELECT value, expires_at FROM cache_entries WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        if row:
            value_str, expires_at = row
            if expires_at > now:
                return json.loads(value_str)
            else:
                # Expired
                delete_cached(key)
        return None
    except Exception:
        return None

def set_cached(key: str, value: Any, ttl_seconds: int = 600):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        expires_at = time.time() + ttl_seconds
        value_str = json.dumps(value)
        cursor.execute("""
            INSERT INTO cache_entries (key, value, expires_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, expires_at = excluded.expires_at
        """, (key, value_str, expires_at))
        conn.commit()
        conn.close()
    except Exception:
        pass

def delete_cached(key: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
        conn.commit()
        conn.close()
    except Exception:
        pass

init_cache()
