"""Group management service (Fase 8)."""

from __future__ import annotations

import asyncio

from src.services.whatsapp.sender.helpers import _ensure_client
from src.utils.logger import logger


def _jid_str(jid) -> str:
    try:
        return f"{jid.User}@{jid.Server}"
    except Exception:
        return str(jid)


def _group_to_dict(g) -> dict:
    participants = []
    for p in getattr(g, "Participants", []) or []:
        participants.append({
            "jid": _jid_str(getattr(p, "JID", None)),
            "lid": getattr(p, "LID", None),
            "phoneNumber": getattr(p, "PhoneNumber", None),
            "isAdmin": bool(getattr(p, "IsAdmin", False)),
            "isSuperAdmin": bool(getattr(p, "IsSuperAdmin", False)),
            "displayName": getattr(p, "DisplayName", None),
            "error": getattr(p, "Error", None),
        })
    return {
        "jid": _jid_str(getattr(g, "JID", None)),
        "name": getattr(g, "GroupName", None),
        "topic": getattr(g, "GroupTopic", None),
        "ownerJid": _jid_str(getattr(g, "OwnerJID", None)),
        "created": getattr(g, "GroupCreated", None),
        "locked": bool(getattr(g, "GroupLocked", False)),
        "announce": bool(getattr(g, "GroupAnnounce", False)),
        "ephemeral": getattr(g, "GroupEphemeral", None),
        "participants": participants,
    }


async def list_joined(session_id: str = "1") -> list[dict]:
    client = _ensure_client(session_id)
    groups = await asyncio.to_thread(client.get_joined_groups)
    return [_group_to_dict(g) for g in (groups or [])]


async def get_group(session_id: str, jid: str) -> dict:
    from neonize.utils import build_jid

    client = _ensure_client(session_id)
    info = await asyncio.to_thread(client.get_group_info, build_jid(jid))
    return _group_to_dict(info)


async def create_group(session_id: str, name: str, participants: list[str] | None = None) -> dict:
    from neonize.utils import build_jid

    client = _ensure_client(session_id)
    jids = [build_jid(p) for p in (participants or [])]
    info = await asyncio.to_thread(client.create_group, name, jids)
    return _group_to_dict(info)


async def leave_group(session_id: str, jid: str) -> None:
    from neonize.utils import build_jid

    client = _ensure_client(session_id)
    await asyncio.to_thread(client.leave_group, build_jid(jid))


async def invite_link(session_id: str, jid: str, revoke: bool = False) -> str:
    from neonize.utils import build_jid

    client = _ensure_client(session_id)
    return await asyncio.to_thread(client.get_group_invite_link, build_jid(jid), revoke)


async def update_participants(session_id: str, jid: str, participants: list[str], action: str) -> list[dict]:
    from neonize.utils import build_jid
    from neonize.utils.enum import ParticipantChange

    client = _ensure_client(session_id)
    action_map = {
        "add": ParticipantChange.ADD,
        "remove": ParticipantChange.REMOVE,
        "promote": ParticipantChange.PROMOTE,
        "demote": ParticipantChange.DEMOTE,
    }
    if action not in action_map:
        raise ValueError("invalid action")
    jid_obj = build_jid(jid)
    p_jids = [build_jid(p) for p in participants]
    res = await asyncio.to_thread(client.update_group_participants, jid_obj, p_jids, action_map[action])
    out = []
    for p in res or []:
        out.append({"jid": _jid_str(getattr(p, "JID", None)), "error": getattr(p, "Error", None)})
    return out


async def list_join_requests(session_id: str, jid: str) -> list[dict]:
    from neonize.utils import build_jid

    client = _ensure_client(session_id)
    reqs = await asyncio.to_thread(client.get_group_request_participants, build_jid(jid))
    out = []
    for r in reqs or []:
        participant = getattr(r, "Participant", None)
        out.append({
            "jid": _jid_str(participant),
            "timeAt": getattr(r, "TimeAt", None),
        })
    return out


async def update_join_requests(session_id: str, jid: str, participants: list[str], action: str) -> list[dict]:
    from neonize.utils import build_jid
    from neonize.utils.enum import ParticipantRequestChange

    client = _ensure_client(session_id)
    action_map = {
        "approve": ParticipantRequestChange.APPROVE,
        "reject": ParticipantRequestChange.REJECT,
    }
    if action not in action_map:
        raise ValueError("invalid action")
    jid_obj = build_jid(jid)
    p_jids = [build_jid(p) for p in participants]
    res = await asyncio.to_thread(
        client.update_group_request_participants,
        jid_obj,
        p_jids,
        action_map[action],
    )
    out = []
    for p in res or []:
        out.append({"jid": _jid_str(getattr(p, "JID", None)), "error": getattr(p, "Error", None)})
    return out