import asyncio
import os
from fastapi import HTTPException
from src.services.whatsapp.client import get_sock
from src.services.media.downloader import download_media
from src.utils.logger import logger
from src.controllers.whatsapp.schemas import ProfileUpdateRequest


async def update_my_profile(data: ProfileUpdateRequest):
    temp_file_path = None
    try:
        sock = get_sock()
        if not sock:
            raise HTTPException(status_code=503, detail="WhatsApp não conectado")

        if not data.name and not data.newProfilePictureUrl:
            raise HTTPException(
                status_code=400,
                detail="Informe 'name' ou 'newProfilePictureUrl' para atualizar (envie ao menos um).",
            )

        updates = []

        # ── Nome do perfil (pushname) ──────────────────────
        if data.name:
            await asyncio.to_thread(sock.set_profile_name, data.name)
            updates.append(f"Nome alterado para: {data.name}")

        # ── Foto do perfil ──────────────────────────────────
        if data.newProfilePictureUrl:
            temp_file_path = await download_media(data.newProfilePictureUrl)

            # set_profile_photo aceita str (caminho) ou bytes
            # Retorna PictureID
            picture_id = await asyncio.to_thread(sock.set_profile_photo, temp_file_path)
            updates.append(f"Foto de perfil atualizada (PictureID: {picture_id})")

        logger.info(f"👤 Perfil do bot atualizado: {', '.join(updates)}")
        return {"success": True, "updated": updates}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar perfil do bot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.error(f"Erro ao apagar arquivo temporário: {str(e)}")
