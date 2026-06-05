"""
Shared utility for resolving reply/quote references in outgoing messages.

Eliminates the duplicated quote block that existed across 8 send controllers.
Usage: send controllers call this function instead of reimplementing the logic.
"""

from __future__ import annotations
from typing import Optional, List, Union

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


async def build_send_options(
    jid: str,
    reply_identifier: Optional[str] = None,
    reply_type: Optional[str] = "id",
    delay_message: Optional[Union[int, float, str]] = None,
    delay_typing: Optional[Union[int, float]] = None,
    mentioned: Optional[List[str]] = None,
) -> dict:
    options = await resolve_quote(jid, reply_identifier, reply_type)
    if delay_message is not None:
        options["delay_message"] = delay_message
    if delay_typing is not None:
        options["delay_typing"] = delay_typing
    if mentioned:
        options["mentioned"] = mentioned
    return options
