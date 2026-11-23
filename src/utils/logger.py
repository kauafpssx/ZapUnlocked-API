"""Centralised logging configuration using Loguru.

Provides a logger with:
- stdout output (coloured, filtered)
- File persistence (daily rotation, 30-day retention)
"""

import logging
import re
from loguru import logger
import sys
from pathlib import Path

# Remove default Loguru handler
logger.remove()

# ── Suppress noisy 3rd-party loggers ──────────────────────────────
# watchfiles spams "X changes detected" on every file change during --reload
logging.getLogger("watchfiles").setLevel(logging.WARNING)
# uvicorn error / access logs are handled by Loguru; keep them clean
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# Log directory at project root
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "zapunlocked_{time:YYYY-MM-DD}.log"


_SECRET_QUERY_RE = re.compile(r"([?&](?:API_KEY|api_key)=)[^&\s]+")


def _filter_lid_logs(record):
    """Filter noisy records and redact credentials before any sink sees them."""
    message = record["message"]
    if "Migrated to LID encryption" in message:
        return False
    record["message"] = _SECRET_QUERY_RE.sub(r"\1***", message)
    return True


# Console handler (stdout) with filter
logger.add(
    sys.stdout,
    filter=_filter_lid_logs,
    level="DEBUG",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
)

# File handler with daily rotation and 30-day retention
logger.add(
    str(LOG_FILE),
    rotation="1 day",
    retention="30 days",
    level="INFO",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)
