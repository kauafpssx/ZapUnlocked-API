import asyncio
from src.utils.decorators import require_whatsapp, handle_errors


@require_whatsapp
@handle_errors("list groups")
async def list_groups():
    from src.services.whatsapp.client import get_client
    from neonize.utils.jid import Jid2String

    client = get_client()
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
