"""Global concurrent upload size tracker."""

import asyncio
from src.config.constants import MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_SIZE_MB

_lock = asyncio.Lock()
_current_bytes = 0


async def acquire(size: int) -> bool:
    """Reserve `size` bytes. Returns False if global limit would be exceeded."""
    global _current_bytes
    async with _lock:
        if _current_bytes + size > MAX_UPLOAD_SIZE_BYTES:
            return False
        _current_bytes += size
        return True


async def release(size: int) -> None:
    global _current_bytes
    async with _lock:
        _current_bytes = max(0, _current_bytes - size)


def current_usage_bytes() -> int:
    return _current_bytes


def limit_mb() -> int:
    return MAX_UPLOAD_SIZE_MB
