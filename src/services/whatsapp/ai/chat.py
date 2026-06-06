"""Meta AI integration — send messages to Meta AI and return immediately.

⚠️ IMPORTANT — Meta AI via WhatsApp:
  Meta AI is a special WhatsApp BOT — it uses server type "bot", NOT "s.whatsapp.net".
  Per whatsmeow Go source:
    MetaAIJID    = NewJID("13135550002",        DefaultUserServer)   # OLD (@s.whatsapp.net)
    NewMetaAIJID = NewJID("867051314767696",    BotServer)           # NEW PERSONAL (@bot)
    Business:      718584497008509@bot                                # NEW BUSINESS (@bot)

  • DO NOT use get_lid_from_pn()   — Meta AI is not a regular user
  • DO NOT use is_on_whatsapp()    — Meta AI is not a regular user
  • USE @bot server for new Meta AI, @s.whatsapp.net for legacy only
"""

import asyncio
import os

from neonize.utils.jid import build_jid as neonize_build_jid

from src.utils.logger import logger


# ── Meta AI identifiers ──────────────────────────────────────────────
# Per whatsmeow Go source (types/jid.go):
#   Old:  MetaAIJID    = NewJID("13135550002",     DefaultUserServer)
#   New:  NewMetaAIJID = NewJID("867051314767696", BotServer)
# The Business identifier 718584497008509 also uses @bot.
# ─────────────────────────────────────────────────────────────────────
META_AI_PERSONAL   = os.getenv("META_AI_PERSONAL",   "867051314767696")
META_AI_BUSINESS   = os.getenv("META_AI_BUSINESS",   "718584497008509")
META_AI_LEGACY     = os.getenv("META_AI_LEGACY",     "13135550002")
META_AI_SERVER     = os.getenv("META_AI_SERVER",     "bot")  # or "s.whatsapp.net" for legacy


async def _pick_meta_ai_id(client) -> tuple[str, str]:
    """Pick (identifier, server) for Meta AI based on account type and env config."""
    override = os.getenv("META_AI_PHONE")
    if override:
        return (override, "s.whatsapp.net")  # legacy override

    # smbi = WA Business iOS, smba = WA Business Android, smbw = WA Business Web
    _BUSINESS_PLATFORMS = {"smbi", "smba", "smbw", "smb"}
    try:
        me = await asyncio.to_thread(client.get_me)
        business_name = getattr(me, "BusinessName", None) or ""
        platform = (getattr(me, "Platform", None) or "").lower()
        is_business = bool(business_name) or platform in _BUSINESS_PLATFORMS
        logger.debug(f"[Meta AI] BusinessName={business_name!r} Platform={platform!r} → is_business={is_business}")
        if is_business:
            logger.info(f"[Meta AI] Business account (platform={platform!r}) — using Business Meta AI ID ({META_AI_BUSINESS}@{META_AI_SERVER})")
            return (META_AI_BUSINESS, META_AI_SERVER)
    except Exception as e:
        logger.warning(f"[Meta AI] get_me() failed: {e}")

    logger.debug("Personal account — using Personal Meta AI ID")
    return (META_AI_PERSONAL, META_AI_SERVER)


_RESPONSE_TIMEOUT = int(os.getenv("META_AI_TIMEOUT", "30"))
_CHUNK_SILENCE = float(os.getenv("META_AI_CHUNK_SILENCE", "3"))  # seconds of silence = end of response


async def ask_meta_ai(message: str, wait_response: bool = True, chunk_silence: float = None, stop_on_image: bool = False) -> dict:
    """Send text message to Meta AI.

    Collects all response chunks until META_AI_CHUNK_SILENCE seconds of silence,
    then returns the concatenated text. Total wait capped at META_AI_TIMEOUT.
    """
    from src.services.whatsapp.client import get_client, get_is_ready
    from src.services.whatsapp.ai.response_tracker import set_pending, cleanup

    client = get_client()
    if not client or not get_is_ready():
        raise Exception("WhatsApp not connected.")

    identifier, server = await _pick_meta_ai_id(client)
    jid = neonize_build_jid(identifier, server)
    jid_str = f"{identifier}@{server}"

    queue: asyncio.Queue = asyncio.Queue()
    request_id = f"ask_{id(queue)}"
    if wait_response:
        set_pending(request_id, queue)

    logger.info(f"🤖 Sending to Meta AI ({jid_str}): {message!r}")

    try:
        res = await asyncio.to_thread(client.send_message, jid, message)
        msg_id = getattr(res, "ID", None)
    except Exception as e:
        if wait_response:
            cleanup(request_id)
        error_msg = str(e)
        if "no LID found" in error_msg:
            raise Exception(
                f"WhatsApp couldn't reach Meta AI ({jid_str}). "
                "Causes: (1) Meta AI not available in your region, "
                "(2) send a message to Meta AI from your phone first, "
                "(3) set META_AI_SERVER=s.whatsapp.net for legacy number."
            )
        raise

    if not wait_response:
        cleanup(request_id)
        return {"messageId": msg_id}

    silence = chunk_silence if chunk_silence is not None else _CHUNK_SILENCE
    # Collect chunks until silence seconds of silence or _RESPONSE_TIMEOUT total
    chunks: list[dict] = []
    deadline = asyncio.get_event_loop().time() + _RESPONSE_TIMEOUT
    try:
        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                break
            wait = min(silence, remaining)
            try:
                chunk = await asyncio.wait_for(queue.get(), timeout=wait)
                chunks.append(chunk)
                if stop_on_image and chunk.get("hasImage"):
                    break  # got the image chunk — done immediately
            except asyncio.TimeoutError:
                if stop_on_image:
                    pass  # keep waiting for image until total deadline
                elif chunks:
                    break  # silence window expired after at least one chunk = done
                # no chunks yet — keep waiting until total deadline
    finally:
        cleanup(request_id)

    if not chunks:
        logger.warning(f"Meta AI response timed out after {_RESPONSE_TIMEOUT}s")
        return {"messageId": msg_id}

    # Meta AI sends streaming edits — each edit contains the FULL accumulated text so far.
    # Use the last chunk with text as the final answer.
    has_image = any(c.get("hasImage") for c in chunks)
    last_text = next((c["text"] for c in reversed(chunks) if c.get("text")), "")
    image_chunk = next((c for c in reversed(chunks) if c.get("hasImage") and c.get("imageBase64")), None)
    return {
        "messageId": msg_id,
        "text": last_text,
        "hasImage": has_image,
        "imageBase64": image_chunk.get("imageBase64") if image_chunk else None,
        "imageUrl": image_chunk.get("imageUrl") if image_chunk else None,
        "mimeType": image_chunk.get("mimeType") if image_chunk else None,
    }


async def imagine_meta_ai(prompt: str) -> dict:
    """Send image generation prompt to Meta AI. Returns as soon as image chunk arrives."""
    return await ask_meta_ai(f"/imagine {prompt}", stop_on_image=True)
