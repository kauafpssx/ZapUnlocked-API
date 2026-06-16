"""SQLite database cleanup and scheduler for the Neonize auth database."""

import asyncio
import sqlite3
import time
from pathlib import Path

from src.utils.logger import logger
from src.utils.db import get_conn
from src.services.whatsapp import state

DEFAULT_INTERVAL = 1440  # minutes

# Per-session in-memory config cache (loaded from DB at startup)
_session_config: dict[str, dict] = {}


def _get_config(session_id: str = "1") -> dict:
    if session_id not in _session_config:
        _session_config[session_id] = {"interval": DEFAULT_INTERVAL, "last_run": 0}
    return _session_config[session_id]


# ══════════════════════════════════════════════════════════
# CONFIG PERSISTENCE
# ══════════════════════════════════════════════════════════

def load_db_config(session_id: str = "1") -> None:
    cfg = _get_config(session_id)
    try:
        conn = get_conn()
        row = conn.execute(
            "SELECT interval, last_run FROM db_config WHERE session_id=?", (session_id,)
        ).fetchone()
        if row:
            cfg["interval"] = row["interval"]
            cfg["last_run"] = row["last_run"]
    except Exception as e:
        logger.error(f"Error loading db config (session={session_id}): {e}")


def save_db_config(session_id: str = "1") -> None:
    cfg = _get_config(session_id)
    try:
        conn = get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO db_config (session_id, interval, last_run) VALUES (?, ?, ?)",
            (session_id, cfg["interval"], cfg["last_run"]),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving db config (session={session_id}): {e}")


def set_cleanup_interval(interval_minutes: int, session_id: str = "1") -> None:
    _get_config(session_id)["interval"] = interval_minutes
    save_db_config(session_id)
    logger.info(f"⚙️ Cleanup interval updated to {interval_minutes} minutes (session={session_id})")


def get_cleanup_state(session_id: str = "1") -> dict:
    cfg = _get_config(session_id)
    return {"last_cleanup_time": cfg["last_run"], "current_interval": cfg["interval"]}


# ══════════════════════════════════════════════════════════
# CLEANUP
# ══════════════════════════════════════════════════════════

def cleanup_db(session_id: str = "1") -> None:
    """Clean temporary SQLite tables and run VACUUM (thread-safe)."""
    from src.config.constants import get_auth_dir
    cfg = _get_config(session_id)
    cleanup_lock = state.get_cleanup_lock(session_id)
    if not cleanup_lock.acquire(blocking=False):
        logger.warning(f"⚠️ Cleanup already in progress for session={session_id}. Skipping...")
        return

    try:
        auth_file = Path(get_auth_dir(session_id)) / "auth.sqlite"
        if not auth_file.exists():
            return

        logger.info(f"🧹 Starting SQLite cleanup (session={session_id})...")

        conn = sqlite3.connect(str(auth_file), isolation_level=None)
        cursor = conn.cursor()

        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
        except sqlite3.Error as e:
            logger.warning(f"⚠️ Failed to enable WAL mode: {e}")

        cursor.execute("BEGIN TRANSACTION")
        for table in ["whatsmeow_event_buffer"]:
            try:
                cursor.execute(f"DELETE FROM {table}")
                logger.debug(f"Removed records from table {table}")
            except sqlite3.OperationalError:
                pass
        cursor.execute("COMMIT")

        try:
            cursor.execute("VACUUM")
        except sqlite3.Error as e:
            logger.error(f"❌ Error executing VACUUM: {e}")

        conn.close()

        cfg["last_run"] = int(time.time())
        save_db_config(session_id)
        logger.info(f"✅ Database cleanup completed (session={session_id}).")
    except Exception as e:
        logger.error(f"❌ Database cleanup failed (session={session_id}): {e}")
    finally:
        state.get_cleanup_lock(session_id).release()


async def db_cleanup_scheduler(session_id: str = "1") -> None:
    """Infinite loop that runs cleanup periodically per configured interval."""
    while True:
        cfg = _get_config(session_id)
        now = int(time.time())
        elapsed = (now - cfg["last_run"]) / 60
        if elapsed >= cfg["interval"]:
            cleanup_db(session_id)
        await asyncio.sleep(60)
