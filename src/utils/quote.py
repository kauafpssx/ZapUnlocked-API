"""
Shared utility for resolving reply/quote references in outgoing messages.

Eliminates the duplicated quote block that existed across 8 send controllers.
Usage: send controllers call this function instead of reimplementing the logic.
"""

from src.services.whatsapp.sender import find_message


async def resolve_quote(
    jid: str,
    reply_identifier: str | None = None,
    reply_type: str | None = "id",
) -> dict:
    """
    Resolve a quoted message (reply/quote) from local history.

    Args:
        jid: Full recipient JID (e.g. "5511999999999@s.whatsapp.net")
        reply_identifier: Message ID or search text
        reply_type: "id" (default) to look up by ID, "text" to search by content

    Returns:
        Dict with "quoted" key if found, empty dict otherwise.

    Raises:
        Exception: If reply_type=="text" and the message is not found.
    """
    if not reply_identifier:
        return {}

    quoted_msg = await find_message(jid, reply_identifier, reply_type)
    if quoted_msg:
        return {"quoted": quoted_msg}

    if reply_type == "id":
        # Stub so WhatsApp still renders the quote even if the message is not in local history
        return {
            "quoted": {
                "key": {
                    "remoteJid": jid,
                    "fromMe": False,
                    "id": reply_identifier,
                },
                "message": {"conversation": "..."},
            }
        }

    raise Exception(
        f"Could not find the message to quote with text: '{reply_identifier}'"
    )
