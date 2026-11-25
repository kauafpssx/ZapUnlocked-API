"""Group controllers."""

from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException, Query, Request
from pydantic import BaseModel

from src.utils.decorators import get_session_id
from src.services.whatsapp import groups as group_service


class CreateGroupRequest(BaseModel):
    name: str
    participants: Optional[List[str]] = None


class ParticipantsRequest(BaseModel):
    participants: List[str]
    action: str = "add"


class GroupSettingsRequest(BaseModel):
    name: Optional[str] = None
    topic: Optional[str] = None
    announce: Optional[bool] = None
    locked: Optional[bool] = None


async def list_groups(request: Request):
    sid = get_session_id(request)
    try:
        return {"success": True, "groups": await group_service.list_joined(sid)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})


async def get_group(jid: str, request: Request):
    sid = get_session_id(request)
    try:
        return {"success": True, "group": await group_service.get_group(sid, jid)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})


async def create_group(data: CreateGroupRequest, request: Request):
    sid = get_session_id(request)
    try:
        return {"success": True, "group": await group_service.create_group(sid, data.name, data.participants)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})


async def leave_group(jid: str, request: Request):
    sid = get_session_id(request)
    try:
        await group_service.leave_group(sid, jid)
        return {"success": True, "jid": jid}
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})


async def invite_link(jid: str, request: Request, revoke: bool = Query(False)):
    sid = get_session_id(request)
    try:
        link = await group_service.invite_link(sid, jid, revoke)
        return {"success": True, "jid": jid, "inviteLink": link}
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})


async def update_participants(jid: str, data: ParticipantsRequest, request: Request):
    sid = get_session_id(request)
    try:
        res = await group_service.update_participants(sid, jid, data.participants, data.action)
        return {"success": True, "jid": jid, "results": res}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "INVALID_ACTION", "message": str(exc)})
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})


class JoinRequestsRequest(BaseModel):
    participants: List[str]
    action: str = "approve"


async def update_settings(jid: str, data: GroupSettingsRequest, request: Request):
    sid = get_session_id(request)
    try:
        await group_service.update_settings(sid, jid, data.name, data.topic, data.announce, data.locked)
        return {"success": True, "jid": jid}
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})


async def list_join_requests(jid: str, request: Request):
    sid = get_session_id(request)
    try:
        return {"success": True, "jid": jid, "requests": await group_service.list_join_requests(sid, jid)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})


async def update_join_requests(jid: str, data: JoinRequestsRequest, request: Request):
    sid = get_session_id(request)
    try:
        res = await group_service.update_join_requests(sid, jid, data.participants, data.action)
        return {"success": True, "jid": jid, "results": res}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "INVALID_ACTION", "message": str(exc)})
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})