"""
Neonize event callbacks and incoming message processing.

Each handler reads/writes state through the functional API in
src.services.whatsapp.state — never through direct module-level variables.

Handler registration lives in client.py; the actual handler logic lives
in the events/ subpackage for maintainability. This file re-exports
everything so existing imports keep working.
"""

import asyncio
import gc
import time

from neonize.client import NewClient
from neonize.events import MessageEv

from src.utils.logger import logger
from src.config.url_builder import build_qr_url
from src.services.whatsapp import state
from src.services.whatsapp import storage


# ═══════════════════════════════════════════════════════════════════════════
# THREAD-SAFE COROUTINE SCHEDULER
# ═══════════════════════════════════════════════════════════════════════════

def _run_in_loop(coro_factory):
    """Schedule a coroutine in the main event loop (thread-safe).

    Args:
        coro_factory: A callable that returns an awaitable coroutine.
    """
    loop = state.get_main_loop()
    if loop and loop.is_running():
        loop.call_soon_threadsafe(lambda: asyncio.create_task(coro_factory()))


# ═══════════════════════════════════════════════════════════════════════════
# WEBHOOK DISPATCH
# ═══════════════════════════════════════════════════════════════════════════

async def _fire(event_type: str, data: dict) -> None:
    """Dispatch event to the named webhooks system."""
    try:
        from src.services.webhooks.dispatcher import dispatch_event
        await dispatch_event(event_type, data)
    except Exception as e:
        logger.error(f"Error dispatching event '{event_type}': {e}")


# ═══════════════════════════════════════════════════════════════════════════
# NEONIZE EVENT HANDLERS
#
# NOTE: These are called from NEONIZE's Go runtime (separate thread).
# All coroutine dispatch goes through _run_in_loop().
# ═══════════════════════════════════════════════════════════════════════════

# ── QR ────────────────────────────────────────────────────────────────────

def _on_qr(c: NewClient, qr_bytes: bytes) -> None:
    """Handle QR code event from Neonize."""
    if state.get_is_ready():
        return

    if not state.get_qr_url_logged():
        state.set_qr_url_logged(True)
        logger.info(f"📲 QR dashboard: {build_qr_url()}")

    if not state.get_qr_generation_active():
        logger.debug("🔒 QR ignored — waiting for authenticated access on /qr")
        return

    qr_value = qr_bytes.decode("utf-8")
    state.set_current_qr(qr_value)
    state.set_qr_last_generated_at(time.time())
    logger.info(f"📲 QR Code ready! Access: {build_qr_url()}")

    _run_in_loop(lambda: _fire("connection.qr_ready", {"qr": state.get_qr()}))


# ── Connection lifecycle ──────────────────────────────────────────────────

def _on_connected(c: NewClient, event) -> None:
    """Handle successful connection."""
    state.mark_connected()
    logger.info("✅ WhatsApp connected and ready")

    phone = ""
    try:
        me = c.get_me()
        phone = me.JID.User
    except Exception:
        pass

    _run_in_loop(lambda: _fire("connection.connected", {"phone": phone}))


def _on_pair_code(c: NewClient, code: str, connected: bool) -> None:
    """Handle pairing code event."""
    if not connected:
        state.set_current_pair_code(code)
        logger.info(f"🔑 Pairing code received: {code}")
        _run_in_loop(lambda: _fire("connection.pair_code", {"code": code}))
    else:
        _run_in_loop(lambda: _fire("connection.pair_code", {
            "code": code, "connected": True,
        }))


def _on_history_sync(c: NewClient, event) -> None:
    """Skip history sync to conserve RAM."""
    pass


def _on_logged_out(c: NewClient, event) -> None:
    """Handle remote logout."""
    logger.warning(f"🔌 Session logged out — reason: {event.Reason}")
    _run_in_loop(lambda: _fire("connection.logged_out", {"reason": event.Reason}))


def _on_connect_failure(c: NewClient, event) -> None:
    """Handle connection failure."""
    logger.error(f"❌ Connect failure: {event.Reason} — {event.Message}")
    _run_in_loop(lambda: _fire("connection.connect_failure", {
        "reason": event.Reason, "message": event.Message,
    }))


def _on_stream_error(c: NewClient, event) -> None:
    """Handle stream-level errors."""
    logger.error(f"🌊 Stream error — code: {event.Code}")
    _run_in_loop(lambda: _fire("connection.stream_error", {"code": event.Code}))


def _on_temporary_ban(c: NewClient, event) -> None:
    """Handle temporary ban."""
    logger.warning(f"🚫 Temporary ban — code: {event.Code}, expires: {event.Expire}")
    _run_in_loop(lambda: _fire("connection.temporary_ban", {
        "code": event.Code, "expire": event.Expire,
    }))


def _on_client_outdated(c: NewClient, event) -> None:
    """Handle outdated client version."""
    logger.error("⚠️ Client outdated — update required")
    _run_in_loop(lambda: _fire("connection.client_outdated", {}))


def _on_stream_replaced(c: NewClient, event) -> None:
    """Handle stream replaced by another session."""
    logger.warning("🔄 Stream replaced by another session")
    _run_in_loop(lambda: _fire("connection.stream_replaced", {}))


def _on_pair_status(c: NewClient, event) -> None:
    """Handle pairing status changes."""
    try:
        from neonize.utils.jid import Jid2String
        jid_str = Jid2String(event.ID) if event.ID else ""
    except Exception:
        jid_str = ""
    logger.info(f"🔑 Pair status — JID: {jid_str}, status: {event.Status}, business: {event.BusinessName}")
    _run_in_loop(lambda: _fire("connection.pair_status", {
        "jid": jid_str,
        "businessName": event.BusinessName,
        "platform": event.Platform,
        "status": event.Status,
        "error": event.Error,
    }))


# ── Groups ────────────────────────────────────────────────────────────────

def _on_joined_group(c: NewClient, event) -> None:
    """Handle joining a group."""
    try:
        from neonize.utils.jid import Jid2String
        gid = Jid2String(event.GroupInfo.JID) if event.GroupInfo.JID else ""
    except Exception:
        gid = ""
    name = getattr(event.GroupInfo, "Name", "") or ""
    logger.info(f"👥 Joined group: {name} ({gid}) — reason: {event.Reason}")
    _run_in_loop(lambda: _fire("group.join", {
        "groupId": gid, "groupName": name,
        "reason": event.Reason, "type": event.Type,
    }))


def _on_group_info(c: NewClient, event) -> None:
    """Handle group info changes."""
    try:
        from neonize.utils.jid import Jid2String
        jid_str = Jid2String(event.JID) if event.JID else ""
        sender_str = Jid2String(event.Sender) if event.Sender else ""
    except Exception:
        jid_str = ""
        sender_str = ""
    logger.info(f"👥 Group update: {jid_str} — name: {event.Name}")
    _run_in_loop(lambda: _fire("group.update", {
        "groupId": jid_str,
        "sender": sender_str,
        "name": event.Name if event.Name else None,
        "topic": event.Topic if event.Topic else None,
        "locked": event.Locked,
        "announce": event.Announce,
        "ephemeral": event.Ephemeral,
        "delete": event.Delete if event.Delete else False,
        "link": event.Link if event.Link else None,
        "unlink": event.Unlink if event.Unlink else None,
        "newInviteLink": event.NewInviteLink if event.NewInviteLink else None,
    }))


# ── Contact / Presence ────────────────────────────────────────────────────

def _on_presence(c: NewClient, event) -> None:
    """Handle contact presence change."""
    try:
        from neonize.utils.jid import Jid2String
        from_jid = Jid2String(event.From) if event.From else ""
    except Exception:
        from_jid = ""
    phone = from_jid.split("@")[0] if from_jid else ""
    status = "offline" if event.Unavailable else "online"
    logger.debug(f"📍 Presence: {phone} is now {status}")
    _run_in_loop(lambda: _fire("contact.presence", {
        "from": phone, "fromJid": from_jid,
        "status": status, "lastSeen": event.LastSeen,
    }))


def _on_chat_presence(c: NewClient, event) -> None:
    """Handle typing/recording indicators."""
    try:
        from neonize.utils.jid import Jid2String
        src = event.MessageSource
        chat = src.Chat
        jid_str = f"{chat.User}@s.whatsapp.net"
        if src.IsGroup:
            jid_str = f"{chat.User}@g.us"
    except Exception:
        jid_str = ""
    phone = jid_str.split("@")[0] if jid_str else ""
    logger.debug(f"💬 Chat presence: {phone} — {event.State}")
    _run_in_loop(lambda: _fire("contact.chat_presence", {
        "from": phone, "fromJid": jid_str,
        "state": event.State, "media": event.Media if event.Media else None,
    }))


def _on_picture(c: NewClient, event) -> None:
    """Handle profile picture changes."""
    try:
        from neonize.utils.jid import Jid2String
        jid_str = Jid2String(event.JID) if event.JID else ""
        author_str = Jid2String(event.Author) if event.Author else ""
    except Exception:
        jid_str = ""
        author_str = ""
    phone = jid_str.split("@")[0] if jid_str else ""
    action = "removed" if event.Remove else "changed"
    logger.info(f"🖼️ Profile picture {action}: {phone}")
    _run_in_loop(lambda: _fire("contact.picture_change", {
        "from": phone, "fromJid": jid_str,
        "author": author_str, "action": action,
    }))


def _on_identity_change(c: NewClient, event) -> None:
    """Handle encryption identity changes."""
    try:
        from neonize.utils.jid import Jid2String
        jid_str = Jid2String(event.JID) if event.JID else ""
    except Exception:
        jid_str = ""
    phone = jid_str.split("@")[0] if jid_str else ""
    logger.info(f"🔐 Identity changed: {phone} (implicit: {event.Implicit})")
    _run_in_loop(lambda: _fire("contact.identity_change", {
        "from": phone, "fromJid": jid_str,
        "implicit": event.Implicit, "timestamp": event.Timestamp,
    }))


# ── Read / Delivery receipts ──────────────────────────────────────────────

def _on_receipt(c: NewClient, event) -> None:
    """Handle message read/delivery receipts."""
    try:
        from neonize.utils.jid import Jid2String
        src = event.MessageSource
        chat = src.Chat
        jid_str = f"{chat.User}@s.whatsapp.net"
        if src.IsGroup:
            jid_str = f"{chat.User}@g.us"
    except Exception:
        jid_str = ""
    phone = jid_str.split("@")[0] if jid_str else ""
    msg_ids = list(event.MessageIDs) if event.MessageIDs else []
    logger.debug(f"📨 Receipt: {phone} — type={event.Type}, ids={len(msg_ids)}")
    event_name = {1: "message.delivered", 4: "message.read"}.get(event.Type, "message.receipt")
    _run_in_loop(lambda: _fire(event_name, {
        "from": phone, "fromJid": jid_str,
        "messageIds": msg_ids, "type": event.Type,
        "timestamp": event.Timestamp,
    }))


# ── Calls ─────────────────────────────────────────────────────────────────

def _on_call_offer(c: NewClient, event) -> None:
    """Handle incoming call — reject automatically if configured."""
    try:
        from src.services.whatsapp.settingsService import get_settings
        settings = get_settings()

        meta = event.basicCallMeta
        caller_jid = getattr(meta, "from")
        call_id = meta.callID

        from neonize.utils.jid import Jid2String
        caller_str = Jid2String(caller_jid)
        caller_phone = caller_str.split("@")[0]

        _run_in_loop(lambda: _fire("call.received", {
            "from": caller_phone, "fromJid": caller_str, "callId": call_id,
        }))

        if not settings.get("call_reject_auto", False):
            return

        logger.info(f"📞 Call from {caller_str} (ID: {call_id}) — rejecting automatically")

        msg = settings.get("call_reject_message", "")
        if msg:
            async def _send_call_reply():
                try:
                    c.send_message(caller_jid, msg)
                    logger.info(f"📞 Rejection message sent to {caller_str}")
                except Exception as send_err:
                    logger.warning(f"⚠️ Failed to send rejection message: {send_err}")
            _run_in_loop(_send_call_reply)
    except Exception as e:
        logger.error(f"Error in call handler: {e}")


def _on_call_accept(c: NewClient, event) -> None:
    """Handle call accepted."""
    try:
        meta = event.basicCallMeta
        from neonize.utils.jid import Jid2String
        caller_jid = getattr(meta, "from")
        caller_str = Jid2String(caller_jid)
        caller_phone = caller_str.split("@")[0]
    except Exception:
        caller_phone = ""
        caller_str = ""
    logger.info(f"📞 Call accepted: {caller_phone}")
    _run_in_loop(lambda: _fire("call.accepted", {
        "from": caller_phone, "fromJid": caller_str,
        "callId": getattr(meta, "callID", ""),
    }))


def _on_call_terminate(c: NewClient, event) -> None:
    """Handle call ended."""
    try:
        meta = event.basicCallMeta
        from neonize.utils.jid import Jid2String
        caller_jid = getattr(meta, "from")
        caller_str = Jid2String(caller_jid)
        caller_phone = caller_str.split("@")[0]
    except Exception:
        caller_phone = ""
        caller_str = ""
    logger.info(f"📞 Call terminated: {caller_phone} — reason: {event.reason}")
    _run_in_loop(lambda: _fire("call.terminated", {
        "from": caller_phone, "fromJid": caller_str,
        "callId": getattr(meta, "callID", ""),
        "reason": event.reason,
    }))


# ── Undecryptable messages ────────────────────────────────────────────────

def _on_undecryptable(c: NewClient, event) -> None:
    """Handle undecryptable messages."""
    try:
        from neonize.utils.jid import Jid2String
        src = event.Info.MessageSource
        chat = src.Chat
        jid_str = f"{chat.User}@s.whatsapp.net"
        if src.IsGroup:
            jid_str = f"{chat.User}@g.us"
    except Exception:
        jid_str = ""
    phone = jid_str.split("@")[0] if jid_str else ""
    logger.warning(f"🔒 Undecryptable message from: {phone}")
    _run_in_loop(lambda: _fire("message.undecryptable", {
        "from": phone, "fromJid": jid_str,
    }))


# ── Messages ──────────────────────────────────────────────────────────────

def _on_message(c: NewClient, message: MessageEv) -> None:
    """Schedule received message processing in the main event loop."""
    if message.Info.Timestamp < state.get_start_time() - 10:
        return
    try:
        loop = state.get_main_loop()
        if loop and loop.is_running():
            loop.call_soon_threadsafe(
                lambda: asyncio.create_task(handle_message_async(c, message))
            )
        else:
            logger.warning("🕒 Main loop not available to process message")
    except Exception as e:
        logger.error(f"Error scheduling message: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# MESSAGE PROCESSING PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

async def handle_message_async(c: NewClient, message: MessageEv) -> None:
    """Process received message: filter, persist, webhook, auto-read, handlers."""
    ts = message.Info.Timestamp
    if ts < state.get_start_time() - 10 or message.Info.MessageSource.Chat.User == "status":
        return

    from src.utils.parsing.message_parser import parse_message, should_ignore_message

    if should_ignore_message(message):
        return

    source = message.Info.MessageSource
    chat = source.Chat

    jid = _resolve_jid(source, chat)

    phone = jid.split("@")[0]

    parsed = parse_message(message)
    if not parsed:
        _cache_reaction_if_present(message)
        return

    _cache_reaction_if_present(message)

    text_content = parsed.get("text", "")
    resolved_name = message.Info.Pushname or phone

    msg_dict = {
        "key": {
            "remoteJid": jid,
            "fromMe": source.IsFromMe,
            "id": message.Info.ID,
        },
        "messageTimestamp": int(ts),
        "pushName": resolved_name,
        "message": {"conversation": text_content} if text_content else {},
    }

    await storage.add_message_to_history(phone, msg_dict)
    await storage.save_chat_index({
        "id": jid,
        "phone": phone,
        "name": resolved_name,
        "lastMessageTimestamp": int(ts),
    })

    _auto_read_message(c, message, source)
    _forward_to_handler(c, message)

    if ts % 10 == 0:
        gc.collect()


def _resolve_jid(source, chat) -> str:
    """Resolve the JID (WhatsApp ID) from a message source."""
    jid_suffix = "@g.us" if source.IsGroup else "@s.whatsapp.net"

    if source.IsGroup:
        return f"{chat.User}@g.us"

    if chat.Server == "lid":
        if source.SenderAlt and source.SenderAlt.Server == "s.whatsapp.net":
            return f"{source.SenderAlt.User}@s.whatsapp.net"
        if source.RecipientAlt and source.RecipientAlt.Server == "s.whatsapp.net":
            return f"{source.RecipientAlt.User}@s.whatsapp.net"
        if source.Sender and source.Sender.Server == "s.whatsapp.net":
            return f"{source.Sender.User}@s.whatsapp.net"

    return f"{chat.User}{jid_suffix}"


def _cache_reaction_if_present(message) -> None:
    """Extract and cache reaction if present in the message."""
    try:
        reaction = message.Message.reactionMessage
        if reaction and reaction.key.ID:
            state.get_reaction_cache()[reaction.key.ID] = reaction.text
    except Exception:
        pass


def _auto_read_message(c, message, source) -> None:
    """Mark message as read automatically if configured."""
    try:
        from src.services.whatsapp.settingsService import get_settings
        settings = get_settings()
        if settings.get("auto_read_message", False) and not source.IsFromMe:
            from neonize.utils.enum import ReceiptType
            c.mark_read(
                message.Info.ID,
                chat=source.Chat,
                sender=source.Sender,
                receipt=ReceiptType.READ,
            )
    except Exception as e:
        logger.debug(f"Auto-read failed: {e}")


def _forward_to_handler(c, message) -> None:
    """Forward message to the callback handler."""
    try:
        from src.handlers import handleMessage
        asyncio.create_task(handleMessage(c, message))
    except Exception:
        pass

