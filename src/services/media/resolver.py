"""Unified media source resolver — URL or file upload, with global size tracking and MIME validation."""

import os
from typing import Optional

import httpx
from fastapi import HTTPException, UploadFile

from src.config.constants import MAX_UPLOAD_SIZE_MB
from src.services.media.downloader import download_media
from src.services.media.upload import save_upload
from src.services.media import upload_tracker
from src.services.media.validator import validate_media
from src.utils.logger import logger


async def _head_size(url: str) -> int:
    """HEAD request to get Content-Length. Returns 0 if unknown."""
    try:
        async with httpx.AsyncClient(timeout=5, follow_redirects=True) as client:
            resp = await client.head(url)
            cl = resp.headers.get("content-length")
            return int(cl) if cl else 0
    except Exception:
        return 0


async def resolve_media(
    url: Optional[str],
    file: Optional[UploadFile],
    media_type: Optional[str] = None,
) -> tuple[str, int]:
    """
    Validates source (url XOR file), checks global upload tracker, downloads/saves.
    Returns (temp_path, reserved_bytes).
    Caller MUST call upload_tracker.release(reserved_bytes) + cleanup(temp_path) in finally.
    If media_type is given, validates MIME type against allowlist after obtaining the file.
    """
    has_url = bool(url and url.strip())
    has_file = bool(file and file.filename)

    if has_url and has_file:
        raise HTTPException(status_code=400, detail={
            "error": "AMBIGUOUS_SOURCE",
            "message": "Provide either url or file, not both.",
        })
    if not has_url and not has_file:
        raise HTTPException(status_code=400, detail={
            "error": "MISSING_SOURCE",
            "message": "Provide url or file.",
        })

    if has_url:
        size = await _head_size(url)
        if size > 0:
            if not await upload_tracker.acquire(size):
                raise HTTPException(status_code=413, detail={
                    "error": "UPLOAD_LIMIT_EXCEEDED",
                    "message": f"Global limit of {MAX_UPLOAD_SIZE_MB}MB exceeded. Try again later.",
                })
        try:
            path = await download_media(url)
        except Exception:
            if size > 0:
                await upload_tracker.release(size)
            raise
        # If HEAD gave no size, estimate from downloaded file (best-effort track)
        if size == 0:
            try:
                size = os.path.getsize(path)
                await upload_tracker.acquire(size)
            except Exception:
                size = 0
        if media_type:
            try:
                validate_media(path, media_type)
            except Exception:
                await upload_tracker.release(size)
                import os as _os
                try:
                    _os.remove(path)
                except Exception:
                    pass
                raise
        return path, size

    else:
        size = file.size or 0
        if not await upload_tracker.acquire(size):
            raise HTTPException(status_code=413, detail={
                "error": "UPLOAD_LIMIT_EXCEEDED",
                "message": f"Global limit of {MAX_UPLOAD_SIZE_MB}MB exceeded. Try again later.",
            })
        try:
            path = await save_upload(file)
        except Exception:
            await upload_tracker.release(size)
            raise
        if media_type:
            try:
                validate_media(path, media_type)
            except Exception:
                await upload_tracker.release(size)
                import os as _os
                try:
                    _os.remove(path)
                except Exception:
                    pass
                raise
        return path, size
