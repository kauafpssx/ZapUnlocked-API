"""Central SQLite connection and schema for ZapUnlocked persistent data.

All application data (sessions, settings, stats, webhooks, etc.) live in a
single file at DATA_DIR/zapunlocked.db. Each thread gets its own connection
via threading.local(); WAL mode allows concurrent reads from multiple threads.

Call init_db() once at startup (after DATA_DIR is created).
"""

import sqlite3
import threading
from pathlib import Path

from src.config.constants import DATA_DIR

DB_PATH = Path(DATA_DIR) / "zapunlocked.db"
_local = threading.local()


def get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA synchronous=NORMAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    active      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ip_rules (
    list_name   TEXT NOT NULL CHECK(list_name IN ('whitelist','blacklist')),
    ip          TEXT NOT NULL,
    PRIMARY KEY (list_name, ip)
);

CREATE TABLE IF NOT EXISTS settings (
    session_id  TEXT NOT NULL,
    key         TEXT NOT NULL,
    value       TEXT NOT NULL,
    PRIMARY KEY (session_id, key)
);

CREATE TABLE IF NOT EXISTS stats (
    session_id  TEXT NOT NULL,
    key         TEXT NOT NULL,
    value       INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (session_id, key)
);

CREATE TABLE IF NOT EXISTS webhook_stats (
    session_id    TEXT NOT NULL,
    webhook_name  TEXT NOT NULL,
    fired         INTEGER NOT NULL DEFAULT 0,
    last_fired    TEXT,
    PRIMARY KEY (session_id, webhook_name)
);

CREATE TABLE IF NOT EXISTS webhooks (
    session_id  TEXT NOT NULL,
    name        TEXT NOT NULL,
    url         TEXT NOT NULL,
    method      TEXT NOT NULL DEFAULT 'POST',
    headers     TEXT NOT NULL DEFAULT '{}',
    body        TEXT NOT NULL DEFAULT '{}',
    events      TEXT NOT NULL DEFAULT '["*"]',
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL,
    secret      TEXT,
    PRIMARY KEY (session_id, name)
);

CREATE TABLE IF NOT EXISTS webhook_logs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT NOT NULL,
    webhook_name  TEXT NOT NULL,
    timestamp     TEXT NOT NULL,
    event         TEXT NOT NULL,
    status_code   INTEGER,
    success       INTEGER NOT NULL,
    error         TEXT
);

CREATE INDEX IF NOT EXISTS idx_webhook_logs
    ON webhook_logs(session_id, webhook_name, id);

CREATE TABLE IF NOT EXISTS db_config (
    session_id  TEXT PRIMARY KEY,
    interval    INTEGER NOT NULL DEFAULT 1440,
    last_run    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chat_index (
    session_id              TEXT NOT NULL,
    chat_id                 TEXT NOT NULL,
    phone                   TEXT NOT NULL,
    name                    TEXT,
    last_message_timestamp  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (session_id, chat_id)
);
"""


def init_db() -> None:
    """Create all tables if they don't exist. Safe to call multiple times."""
    conn = get_conn()
    conn.executescript(_SCHEMA)
