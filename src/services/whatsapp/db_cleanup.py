"""SQLite database cleanup and scheduler for the Neonize auth database."""

import asyncio
import gc
import json
import sqlite3
import time
from pathlib import Path

from src.utils.logger import logger
from src.config.constants import AUTH_DIR, DATA_DIR
from src.services.whatsapp import state

DB_CONFIG_FILE = Path(DATA_DIR) / "db_config.json"
DEFAULT_INTERVAL = 1440  # minutes
last_cleanup_time: int = 0
current_interval: int = DEFAULT_INTERVAL


# ══════════════════════════════════════════════════════════
# CONFIG PERSISTENCE
# ══════════════════════════════════════════════════════════

def load_db_config() -> None:
    global current_interval, last_cleanup_time
    try:
        if DB_CONFIG_FILE.exists():
            with open(DB_CONFIG_FILE, "r") as f:
                config = json.load(f)
                current_interval = config.get("interval", DEFAULT_INTERVAL)
                last_cleanup_time = config.get("last_run", 0)
        else:
            current_interval = DEFAULT_INTERVAL
            last_cleanup_time = 0
    except Exception as e:
        logger.error(f"Error loading db config: {e}")


def save_db_config() -> None:
    try:
        with open(DB_CONFIG_FILE, "w") as f:
            json.dump({"interval": current_interval, "last_run": last_cleanup_time}, f)
    except Exception as e:
        logger.error(f"Error saving db config: {e}")


def set_cleanup_interval(interval_minutes: int) -> None:
    """Set the SQLite cleanup interval (in minutes)."""
    global current_interval
    current_interval = interval_minutes
    save_db_config()
    logger.info(f"⚙️ Cleanup interval updated to {interval_minutes} minutes via setter")


def get_cleanup_state() -> dict:
    """Return current cleanup state (for diagnostics)."""
    return {
        "last_cleanup_time": last_cleanup_time,
        "current_interval": current_interval,
    }


# ══════════════════════════════════════════════════════════
# CLEANUP
# ══════════════════════════════════════════════════════════

def cleanup_db() -> None:
    """Clean temporary SQLite tables and run VACUUM (thread-safe)."""
    global last_cleanup_time
    cleanup_lock = state.get_cleanup_lock()
    if not cleanup_lock.acquire(blocking=False):
        logger.warning("⚠️ A cleanup is already in progress. Skipping...")
        return

    try:
        auth_file = Path(AUTH_DIR) / "auth.sqlite"
        if not auth_file.exists():
            return

        logger.info("🧹 Starting automatic SQLite cleanup...")

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
        gc.collect()

        last_cleanup_time = int(time.time())
        save_db_config()
        logger.info("✅ Database cleanup completed successfully.")
    except Exception as e:
        logger.error(f"❌ Database cleanup failed: {e}")
    finally:
        state.get_cleanup_lock().release()


async def db_cleanup_scheduler() -> None:
    """Infinite loop that runs cleanup periodically per configured interval."""
    while True:
        now = int(time.time())
        elapsed = (now - last_cleanup_time) / 60
        if elapsed >= current_interval:
            cleanup_db()
        await asyncio.sleep(60)
