"""Auto-download of received media messages.

Downloads media, encodes as base64, includes in webhook payload, then deletes immediately.
No files are kept on disk.

Controlled by:
  RECEIVE_MEDIA_ENABLED      — default false, opt-in
  RECEIVE_MEDIA_MAX_SIZE_MB  — default 15, skip if file larger (protects against huge videos)
"""

import asyncio
import base64
import os
import uuid
from pathlib import Path

from src.config.constants import TEMP_DIR
from src.utils.logger import logger

_ENABLED = os.getenv("RECEIVE_MEDIA_ENABLED", "false").lower() in ("1", "true", "yes")
_MAX_BYTES = int(os.getenv("RECEIVE_MEDIA_MAX_SIZE_MB", "15")) * 1024 * 1024


def _ext_from_mime(mime: str) -> str:
    if not mime:
        return "bin"
    part = mime.split("/")[-1].split(";")[0].strip()
    return {"jpeg": "jpg", "mpeg": "mp3", "mp4": "mp4", "ogg": "ogg", "webp": "webp"}.get(part, part) or "bin"


async def try_download_media(msg, file_length: int, mime: str, prefix: str, file_name: str = None) -> dict:
    """Download media from a received MessageEv, encode as base64, return in dict.

    Returns:
        {"mediaBase64": "...", "mimeType": "...", "fileName": "...", "mediaTooLarge": False}
        {"mediaBase64": None,   "mimeType": mime,  "fileName": None,  "mediaTooLarge": True}
        {"mediaBase64": None,   "mimeType": mime,  "fileName": None,  "mediaTooLarge": False}
    """
    base_result = {"mediaBase64": None, "mimeType": mime or None, "fileName": file_name or None, "mediaTooLarge": False}

    if not _ENABLED:
        return base_result

    if file_length and file_length > _MAX_BYTES:
        limit_mb = _MAX_BYTES // (1024 * 1024)
        actual_mb = round(file_length / (1024 * 1024), 2)
        logger.debug(f"[MediaReceiver] {prefix} skipped — {actual_mb} MB > limit {limit_mb} MB")
        return {**base_result, "mediaTooLarge": True}

    tmp_path = None
    try:
        from src.services.whatsapp.client import get_client
        client = get_client()

        data: bytes = await asyncio.to_thread(client.download_any, msg.Message)
        if not data:
            return base_result

        ext = _ext_from_mime(mime)
        resolved_name = file_name or f"{prefix}_{uuid.uuid4().hex[:8]}.{ext}"
        b64 = base64.b64encode(data).decode()

        logger.debug(f"[MediaReceiver] Downloaded {prefix} ({len(data)} bytes) → base64")
        return {"mediaBase64": b64, "mimeType": mime or None, "fileName": resolved_name, "mediaTooLarge": False}

    except Exception as e:
        logger.warning(f"[MediaReceiver] Download failed for {prefix}: {e}")
        return base_result
    finally:
        if tmp_path and Path(tmp_path).exists():
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass
