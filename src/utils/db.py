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
    session_id    TEXT NOT NULL,
    name          TEXT NOT NULL,
    url           TEXT NOT NULL,
    method        TEXT NOT NULL DEFAULT 'POST',
    headers       TEXT NOT NULL DEFAULT '{}',
    body          TEXT NOT NULL DEFAULT '{}',
    events        TEXT NOT NULL DEFAULT '["*"]',
    active        INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL,
    secret        TEXT,
    self_destruct INTEGER NOT NULL DEFAULT 0,
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

CREATE TABLE IF NOT EXISTS orders (
    session_id          TEXT NOT NULL,
    order_id            TEXT NOT NULL,
    message_id          TEXT,
    chat_jid            TEXT,
    seller_jid          TEXT,
    whatsapp_status     TEXT,
    local_status        TEXT NOT NULL DEFAULT 'received',
    currency            TEXT,
    subtotal_1000       INTEGER,
    total_1000          INTEGER,
    item_count          INTEGER,
    title               TEXT,
    note                TEXT,
    token               TEXT,
    catalog_id          TEXT,
    surface             TEXT,
    request_message_id  TEXT,
    raw_payload         TEXT,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    PRIMARY KEY (session_id, order_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    order_id        TEXT NOT NULL,
    product_id      TEXT,
    name            TEXT,
    quantity        INTEGER,
    price_1000      INTEGER,
    currency        TEXT,
    image_id        TEXT,
    image_url       TEXT,
    raw_payload     TEXT,
    FOREIGN KEY (session_id, order_id) REFERENCES orders(session_id, order_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_order_items_order
    ON order_items(session_id, order_id);

CREATE TABLE IF NOT EXISTS order_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    order_id        TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    old_status      TEXT,
    new_status      TEXT,
    actor           TEXT,
    metadata        TEXT,
    created_at      TEXT NOT NULL,
    FOREIGN KEY (session_id, order_id) REFERENCES orders(session_id, order_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_order_events_order
    ON order_events(session_id, order_id, id);

CREATE TABLE IF NOT EXISTS payment_references (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    reference_id    TEXT NOT NULL,
    order_id        TEXT,
    amount_1000     INTEGER NOT NULL,
    currency        TEXT NOT NULL,
    pix_key_type    TEXT NOT NULL,
    pix_key_hash    TEXT,
    created_at      TEXT NOT NULL,
    UNIQUE(session_id, reference_id)
);

CREATE TABLE IF NOT EXISTS message_status (
    session_id    TEXT NOT NULL,
    message_id    TEXT NOT NULL,
    chat_jid      TEXT,
    status        TEXT NOT NULL,
    status_rank   INTEGER NOT NULL DEFAULT 0,
    receipt_type  INTEGER,
    timestamp     INTEGER,
    updated_at    TEXT NOT NULL,
    PRIMARY KEY (session_id, message_id)
);

"""

def init_db() -> None:
    """Create all tables if they don't exist. Safe to call multiple times."""
    conn = get_conn()
    conn.executescript(_SCHEMA)
    _run_migrations(conn)


def _run_migrations(conn):
    """Apply incremental schema migrations."""
    try:
        conn.execute("ALTER TABLE webhooks ADD COLUMN self_destruct INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # column already exists
