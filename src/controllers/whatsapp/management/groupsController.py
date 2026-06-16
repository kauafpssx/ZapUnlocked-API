import asyncio
from fastapi import Request
from src.utils.decorators import require_whatsapp, handle_errors, get_session_id


@require_whatsapp
@handle_errors("list groups")
async def list_groups(request: Request = None):
    from src.services.whatsapp import state
    from neonize.utils.jid import Jid2String

    sid = get_session_id(request)
    client = state.get_client(sid)
    groups = await asyncio.to_thread(client.get_joined_groups)

    result = []
    for g in groups:
        try:
            jid_str = Jid2String(g.JID)
            name = getattr(g.GroupName, "Name", None) or ""
            owner = Jid2String(g.OwnerJID) if g.OwnerJID else None
            participant_count = len(g.Participants) if g.Participants else 0
            result.append({
                "groupId": jid_str,
                "name": name,
                "owner": owner,
                "participants": participant_count,
            })
        except Exception:
            pass

    result.sort(key=lambda x: x["name"].lower())
    return {"success": True, "total": len(result), "groups": result}
