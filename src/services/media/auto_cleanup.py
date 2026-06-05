"""Auto cleanup of TEMP_DIR by age and total size."""

import time
from pathlib import Path

from src.config.constants import TEMP_DIR, CLEANUP_MAX_AGE_DAYS, CLEANUP_MAX_SIZE_MB
from src.utils.logger import logger


async def run_media_cleanup() -> None:
    temp = Path(TEMP_DIR)
    if not temp.exists():
        return

    now = time.time()
    cutoff = now - CLEANUP_MAX_AGE_DAYS * 86400
    max_bytes = CLEANUP_MAX_SIZE_MB * 1024 * 1024

    files = [f for f in temp.iterdir() if f.is_file()]
    total_bytes = sum(f.stat().st_size for f in files)
    size_exceeded = total_bytes > max_bytes

    removed = 0
    files_by_age = sorted(files, key=lambda f: f.stat().st_mtime)

    for f in files_by_age:
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
            except Exception as e:
                logger.warning(f"⚠️ Failed to remove {f.name}: {e}")

    if removed:
        logger.info(f"🧹 Media cleanup: removed {removed} file(s) from temp_media")
