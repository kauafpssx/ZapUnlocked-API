"""Download images sent by Meta AI and return base64 + optional persistent URL."""

import asyncio
import base64
import os
import uuid
from pathlib import Path

from src.config.constants import TEMP_DIR, IS_ALWAYSDATA
from src.utils.logger import logger

# Save image to TEMP_DIR and expose via /media only when explicitly requested
# and not running on Alwaysdata (storage-constrained).
_KEEP_IMAGES = os.getenv("META_AI_KEEP_IMAGES", "false").lower() == "true" and not IS_ALWAYSDATA


async def download_meta_ai_image(message) -> dict:
    """Download image from Meta AI message.

    Returns dict with imageBase64, imageUrl (None unless META_AI_KEEP_IMAGES=true
    on non-Alwaysdata), and mimeType.
    """
    from src.services.whatsapp.client import get_client

    client = get_client()

    img_msg = message.Message.imageMessage
    mime = getattr(img_msg, "mimetype", "image/jpeg") or "image/jpeg"
    ext = mime.split("/")[-1].split(";")[0]

    from neonize.utils.enum import MediaType, MediaTypeToMMS

    data = await asyncio.to_thread(
        client.download_media_with_path,
        img_msg.directPath,
        img_msg.fileEncSHA256,
        img_msg.fileSHA256,
        img_msg.mediaKey,
        img_msg.fileLength,
        MediaType.MediaImage,
        MediaTypeToMMS.MediaImage,
    )
    b64 = base64.b64encode(data).decode()

    image_url = None
    if _KEEP_IMAGES:
        filename = f"metaai_{uuid.uuid4().hex}.{ext}"
        path = Path(TEMP_DIR) / filename
        path.write_bytes(data)
        image_url = f"/media/{filename}"
        logger.debug(f"[Meta AI] Image saved: {path}")

    return {"imageBase64": b64, "imageUrl": image_url, "mimeType": mime}
