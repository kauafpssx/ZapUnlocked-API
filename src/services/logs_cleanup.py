"""Log file maintenance — compress old logs to .gz, delete by age and total size.

Env vars:
  LOG_MAX_AGE_DAYS   — delete .gz files older than N days (default: 30)
  LOG_MAX_SIZE_MB    — delete oldest .gz files when total log dir exceeds N MB (default: 50)
"""

import gzip
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

from src.utils.logger import LOG_DIR, logger

_LOG_DIR = Path(LOG_DIR)
_DATE_FMT = "%Y-%m-%d"


def _max_age_days() -> int:
    return int(os.getenv("LOG_MAX_AGE_DAYS", "30"))


def _max_size_bytes() -> int:
    return int(os.getenv("LOG_MAX_SIZE_MB", "50")) * 1024 * 1024


def _today_str() -> str:
    return datetime.now().strftime(_DATE_FMT)


def compress_old_logs() -> int:
    """Compress all .log files that are NOT today's into .gz. Returns count compressed."""
    today = _today_str()
    compressed = 0
    for log_file in _LOG_DIR.glob("zapunlocked_*.log"):
        date_part = log_file.stem.replace("zapunlocked_", "")
        if date_part == today:
            continue  # keep today's live log uncompressed
        gz_path = log_file.with_suffix(".log.gz")
        if gz_path.exists():
            log_file.unlink()  # already compressed, remove plain copy
            continue
        try:
            with open(log_file, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            log_file.unlink()
            compressed += 1
            logger.debug(f"[LogCleanup] Compressed {log_file.name} → {gz_path.name}")
        except Exception as e:
            logger.warning(f"[LogCleanup] Failed to compress {log_file.name}: {e}")
    return compressed


def _all_gz_files() -> list[Path]:
    return sorted(_LOG_DIR.glob("zapunlocked_*.log.gz"))  # oldest first


def cleanup_old_logs() -> int:
    """Delete .gz log files exceeding age or total size limits. Returns count deleted."""
    max_age = _max_age_days()
    max_bytes = _max_size_bytes()
    cutoff = time.time() - max_age * 86400
    removed = 0

    gz_files = _all_gz_files()
    total_bytes = sum(f.stat().st_size for f in gz_files)
    size_exceeded = total_bytes > max_bytes

    for f in gz_files:
        try:
            stat = f.stat()
        except FileNotFoundError:
            continue
        age_exceeded = stat.st_mtime < cutoff
        if age_exceeded or size_exceeded:
            try:
                file_size = stat.st_size
                f.unlink()
                total_bytes -= file_size
                size_exceeded = total_bytes > max_bytes
                removed += 1
                logger.debug(f"[LogCleanup] Deleted {f.name}")
            except Exception as e:
                logger.warning(f"[LogCleanup] Failed to delete {f.name}: {e}")
    return removed


async def run_logs_cleanup() -> dict:
    """Full cycle: compress old logs, then delete by age/size."""
    compressed = compress_old_logs()
    deleted = cleanup_old_logs()
    if compressed or deleted:
        logger.info(f"🗜️ Log cleanup: {compressed} compressed, {deleted} deleted")
    return {"compressed": compressed, "deleted": deleted}
