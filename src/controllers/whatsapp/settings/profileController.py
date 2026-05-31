import asyncio
import os
from fastapi import HTTPException
from src.services.whatsapp.client import get_client
from src.services.media.downloader import download_media
from src.utils.logger import logger
from src.schemas import ProfileUpdateRequest


async def update_my_profile(data: ProfileUpdateRequest):
    temp_file_path = None
    try:
        sock = get_client()
        if not sock:
            raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

        if not data.name and not data.newProfilePictureUrl:
            raise HTTPException(
                status_code=400,
                detail={"error": "MISSING_FIELD", "message": "Provide 'name' or 'newProfilePictureUrl' to update (at least one required)."},
            )

        updates = []

        # ── Profile name (pushname) ────────────────────────
        if data.name:
            await asyncio.to_thread(sock.set_profile_name, data.name)
            updates.append(f"Name changed to: {data.name}")

        # ── Profile photo ─────────────────────────────────
        if data.newProfilePictureUrl:
            temp_file_path = await download_media(data.newProfilePictureUrl)

            # set_profile_photo accepts str (path) or bytes
            # Retorna PictureID
            picture_id = await asyncio.to_thread(sock.set_profile_photo, temp_file_path)
            updates.append(f"Profile photo updated (PictureID: {picture_id})")

        logger.info(f"👤 Bot profile updated: {', '.join(updates)}")
        return {"success": True, "updated": updates}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update bot profile: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.error(f"Failed to delete temp file: {str(e)}")
