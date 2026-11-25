"""Sticker pack sender (Fase 11)."""

from __future__ import annotations

import asyncio

from src.services.whatsapp.sender.helpers import _ensure_client, build_jid, _dispatch_sent_event, _save_to_history
from src.utils.logger import logger


async def send_sticker_pack(jid: str, files: list, packname: str = "Sticker pack", publisher: str = "", session_id: str = "1"):
    client = _ensure_client(session_id)
    msgs = await asyncio.to_thread(client.build_stickerpack_message, files, None, packname, publisher)
    results = []
    for msg in msgs or []:
        res = client.send_message(build_jid(jid), msg)
        results.append(res)
    await _dispatch_sent_event(jid, "sticker_pack", results[-1] if results else None, session_id)
    return results