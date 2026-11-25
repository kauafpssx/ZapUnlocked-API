"""Newsletter/channel service (Fase 9)."""

from __future__ import annotations

import asyncio

from src.services.whatsapp.sender.helpers import _ensure_client
from src.utils.logger import logger


def _jid_str(jid) -> str:
    try:
        return f"{jid.User}@{jid.Server}"
    except Exception:
        return str(jid)


def _meta_to_dict(meta) -> dict:
    tm = getattr(meta, "ThreadMeta", None)
    vm = getattr(meta, "ViewerMeta", None)
    name = getattr(tm, "Name", None)
    desc = getattr(tm, "Description", None)
    return {
        "id": _jid_str(getattr(meta, "ID", None)),
        "state": getattr(getattr(meta, "State", None), "Type", None),
        "name": getattr(name, "Text", None) if name else None,
        "description": getattr(desc, "Text", None) if desc else None,
        "inviteCode": getattr(tm, "InviteCode", None),
        "subscriberCount": getattr(tm, "SubscriberCount", None),
        "verificationState": getattr(tm, "VerificationState", None),
        "mute": getattr(vm, "Mute", None),
        "role": getattr(vm, "Role", None),
    }


async def get_info(session_id: str, jid: str) -> dict:
    from neonize.utils import build_jid

    client = _ensure_client(session_id)
    meta = await asyncio.to_thread(client.get_newsletter_info, build_jid(jid))
    return _meta_to_dict(meta)


async def get_info_by_invite(session_id: str, invite: str) -> dict:
    client = _ensure_client(session_id)
    meta = await asyncio.to_thread(client.get_newsletter_info_with_invite, invite)
    return _meta_to_dict(meta)


async def get_messages(session_id: str, jid: str, count: int = 20, before: int = 0) -> list[dict]:
    from neonize.utils import build_jid

    client = _ensure_client(session_id)
    msgs = await asyncio.to_thread(client.get_newsletter_messages, build_jid(jid), count, before)
    out = []
    for m in msgs or []:
        msg = getattr(m, "Message", None)
        text = None
        if msg is not None:
            text = getattr(msg, "conversation", None) or getattr(getattr(msg, "extendedTextMessage", None), "text", None)
        out.append({
            "serverId": getattr(m, "MessageServerID", None),
            "views": getattr(m, "ViewsCount", None),
            "reactions": getattr(m, "ReactionCounts", None),
            "text": text,
        })
    return out


async def follow(session_id: str, jid: str) -> None:
    from neonize.utils import build_jid

    client = _ensure_client(session_id)
    await asyncio.to_thread(client.follow_newsletter, build_jid(jid))


async def unfollow(session_id: str, jid: str) -> None:
    from neonize.utils import build_jid

    client = _ensure_client(session_id)
    await asyncio.to_thread(client.unfollow_newsletter, build_jid(jid))


async def toggle_mute(session_id: str, jid: str, mute: bool) -> None:
    from neonize.utils import build_jid

    client = _ensure_client(session_id)
    await asyncio.to_thread(client.newsletter_toggle_mute, build_jid(jid), mute)


async def react(session_id: str, jid: str, server_id: int, reaction: str, message_id: str = "") -> None:
    from neonize.utils import build_jid

    client = _ensure_client(session_id)
    await asyncio.to_thread(client.newsletter_send_reaction, build_jid(jid), server_id, reaction, message_id)