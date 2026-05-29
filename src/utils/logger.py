"""Centralised logging configuration using Loguru.

Provides a logger with:
- stdout output (coloured, filtered)
- File persistence (daily rotation, 30-day retention)
"""

from loguru import logger
import sys
from pathlib import Path

# Remove default Loguru handler
logger.remove()

# Log directory at project root
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "zapunlocked_{time:YYYY-MM-DD}.log"


def _filter_lid_logs(record):
    """Filter LID migration noise from Neonize."""
    return "Migrated to LID encryption" not in record["message"]


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
