"""Channel/newsletter controllers."""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Query, Request
from pydantic import BaseModel

from src.utils.decorators import get_session_id
from src.services.whatsapp import channels as channel_service


class ReactRequest(BaseModel):
    server_id: int
    reaction: str
    message_id: Optional[str] = None


class MuteRequest(BaseModel):
    mute: bool = True


async def get_info_by_invite(invite: str, request: Request):
    sid = get_session_id(request)
    try:
        return {"success": True, "channel": await channel_service.get_info_by_invite(sid, invite)}
    except Exception as exc:
        from src.utils.logger import logger
        logger.error(f"get_info_by_invite failed: {exc}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})


async def get_info(jid: str, request: Request):
    sid = get_session_id(request)
    try:
        return {"success": True, "channel": await channel_service.get_info(sid, jid)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})


async def get_messages(jid: str, request: Request, count: int = Query(20), before: int = Query(0)):
    sid = get_session_id(request)
    try:
        msgs = await channel_service.get_messages(sid, jid, count, before)
        return {"success": True, "jid": jid, "messages": msgs}
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})


async def follow(jid: str, request: Request):
    sid = get_session_id(request)
    try:
        await channel_service.follow(sid, jid)
        return {"success": True, "jid": jid, "action": "followed"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})


async def unfollow(jid: str, request: Request):
    sid = get_session_id(request)
    try:
        await channel_service.unfollow(sid, jid)
        return {"success": True, "jid": jid, "action": "unfollowed"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})


async def react(jid: str, data: ReactRequest, request: Request):
    sid = get_session_id(request)
    try:
        await channel_service.react(sid, jid, data.server_id, data.reaction, data.message_id or "")
        return {"success": True, "jid": jid, "serverId": data.server_id, "reaction": data.reaction}
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})


async def mute(jid: str, data: MuteRequest, request: Request):
    sid = get_session_id(request)
    try:
        await channel_service.toggle_mute(sid, jid, data.mute)
        return {"success": True, "jid": jid, "mute": data.mute}
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})