"""
WhatsApp client via Neonize.
Manages connection, events, reconnection and bot lifecycle.
"""

import asyncio
import gc
from pathlib import Path

from neonize.client import NewClient
from neonize.events import ConnectedEv, MessageEv, HistorySyncEv, CallOfferEv
import sqlite3
import json
import time
import logging
from neonize.utils import log as neonize_logger
import sys
import re
import threading
import os
import socket

from src.utils.logger import logger
from src.config.constants import AUTH_DIR, DATA_DIR, RECONNECT_DELAY, PORT, API_KEY
from src.services.whatsapp import storage

# ── Global state ──────────────────────────────────────
client: NewClient | None = None
is_ready = False
current_qr: str | None = None
current_pair_code: str | None = None
reaction_cache: dict = {}
START_TIME = time.time()
main_loop: asyncio.AbstractEventLoop | None = None

# QR generation gating: only store QR after someone accesses /qr with valid key
qr_generation_active: bool = False
qr_last_generated_at: float | None = None
QR_EXPIRY_SECONDS: int = 20
_keep_qr_active_on_restart: bool = False
_qr_url_logged: bool = False  # log dashboard URL only once per session

DB_CONFIG_FILE = Path(DATA_DIR) / "db_config.json"
DEFAULT_INTERVAL = 1440
last_cleanup_time = 0
current_interval = DEFAULT_INTERVAL

MAX_REACTIONS_IN_CACHE = 1000
cleanup_lock = threading.Lock()


# ══════════════════════════════════════════════════════════
# GETTERS / SETTERS
# ══════════════════════════════════════════════════════════

def get_sock():
    return client


def get_is_ready():
    return is_ready


def get_qr():
    return current_qr


def get_pair_code():
    return current_pair_code


def reset_pair_code():
    global current_pair_code
    current_pair_code = None


def activate_qr():
    """Authorize QR storage. Call after valid auth on /qr or /qr/image.
    If already connected: no-op. If QR expired (current_qr=None): restart bot to generate a new one."""
    global qr_generation_active, _keep_qr_active_on_restart
    if is_ready:
        return
    qr_generation_active = True
    if current_qr is None and main_loop and main_loop.is_running():
        _keep_qr_active_on_restart = True
        main_loop.call_soon_threadsafe(
            lambda: asyncio.create_task(start_bot())
        )


def get_qr_expires_in() -> int | None:
    """Remaining seconds of the current QR. None if no QR."""
    if current_qr is None or qr_last_generated_at is None:
        return None
    remaining = QR_EXPIRY_SECONDS - int(time.time() - qr_last_generated_at)
    return max(remaining, 0)


def get_store():
    return None  # Deprecated to conserve RAM


def get_reaction_cache():
    return reaction_cache


def set_cleanup_interval(interval_minutes: int):
    """Set the SQLite database cleanup interval (in minutes)."""
    global current_interval
    current_interval = interval_minutes
    save_db_config()
    logger.info(f"⚙️ Cleanup interval updated to {interval_minutes} minutes via setter")


def get_cleanup_state():
    """Return current cleanup state (for diagnostics)."""
    return {
        "last_cleanup_time": last_cleanup_time,
        "current_interval": current_interval,
    }


# ══════════════════════════════════════════════════════════
# SQLITE DATABASE MANAGEMENT
# ══════════════════════════════════════════════════════════

def load_db_config():
    global current_interval, last_cleanup_time
    try:
        if DB_CONFIG_FILE.exists():
            with open(DB_CONFIG_FILE, "r") as f:
                config = json.load(f)
                current_interval = config.get("interval", DEFAULT_INTERVAL)
                last_cleanup_time = config.get("last_run", 0)
    except Exception as e:
        logger.error(f"Error loading db config: {e}")


def save_db_config():
    try:
        with open(DB_CONFIG_FILE, "w") as f:
            json.dump(
                {"interval": current_interval, "last_run": last_cleanup_time}, f
            )
    except Exception as e:
        logger.error(f"Error saving db config: {e}")


def cleanup_db():
    """Clean temporary SQLite tables and run VACUUM (thread-safe)."""
    global last_cleanup_time
    if not cleanup_lock.acquire(blocking=False):
        logger.warning("⚠️ A cleanup is already in progress. Skipping...")
        return

    try:
        auth_file = Path(AUTH_DIR) / "auth.sqlite"
        if not auth_file.exists():
            return

        logger.info("🧹 Starting automatic SQLite cleanup...")

        conn = sqlite3.connect(str(auth_file), isolation_level=None)
        cursor = conn.cursor()

        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
        except sqlite3.Error as e:
            logger.warning(f"⚠️ Failed to enable WAL mode: {e}")

        cursor.execute("BEGIN TRANSACTION")
        for table in ["whatsmeow_event_buffer"]:
            try:
                cursor.execute(f"DELETE FROM {table}")
                logger.debug(f"Removed records from table {table}")
            except sqlite3.OperationalError:
                pass
        cursor.execute("COMMIT")

        try:
            cursor.execute("VACUUM")
        except sqlite3.Error as e:
            logger.error(f"❌ Error executing VACUUM: {e}")

        conn.close()
        gc.collect()

        last_cleanup_time = int(time.time())
        save_db_config()
        logger.info("✅ Database cleanup completed successfully.")
    except Exception as e:
        logger.error(f"❌ Database cleanup failed: {e}")
    finally:
        cleanup_lock.release()


async def db_cleanup_scheduler():
    """Infinite loop that runs cleanup periodically per configured interval."""
    while True:
        now = int(time.time())
        elapsed = (now - last_cleanup_time) / 60
        if elapsed >= current_interval:
            cleanup_db()
        await asyncio.sleep(60)


# ══════════════════════════════════════════════════════════
# HANDLER DE MENSAGENS RECEBIDAS
# ══════════════════════════════════════════════════════════

async def handle_message_async(c: NewClient, message: "MessageEv"):
    """Process received message: filter, persist, webhook, auto-read, handlers."""
    ts = message.Info.Timestamp
    if ts < START_TIME - 10 or message.Info.MessageSource.Chat.User == "status":
        return

    from src.utils.messageParser import parse_message, should_ignore_message

    if should_ignore_message(message):
        return

    source = message.Info.MessageSource
    chat = source.Chat

    jid = f"{chat.User}@s.whatsapp.net"
    if source.IsGroup:
        jid = f"{chat.User}@g.us"
    elif chat.Server == "lid":
        if source.SenderAlt and source.SenderAlt.Server == "s.whatsapp.net":
            jid = f"{source.SenderAlt.User}@s.whatsapp.net"
        elif source.RecipientAlt and source.RecipientAlt.Server == "s.whatsapp.net":
            jid = f"{source.RecipientAlt.User}@s.whatsapp.net"
        elif source.Sender and source.Sender.Server == "s.whatsapp.net":
            jid = f"{source.Sender.User}@s.whatsapp.net"

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
    await storage.save_chat_index(
        {
            "id": jid,
            "phone": phone,
            "name": resolved_name,
            "lastMessageTimestamp": int(ts),
        }
    )

    _auto_read_message(c, message, source)
    _forward_to_handler(c, message)

    del msg_dict
    if ts % 10 == 0:
        gc.collect()


def _cache_reaction_if_present(message):
    """Extract and cache reaction if present in the message."""
    try:
        reaction = message.Message.reactionMessage
        if reaction and reaction.key.ID:
            reaction_cache[reaction.key.ID] = reaction.text
    except Exception:
        pass


async def _fire(event_type: str, data: dict):
    """Dispatch event to the named webhooks system."""
    try:
        from src.services.webhookDispatcher import dispatch_event
        await dispatch_event(event_type, data)
    except Exception as e:
        logger.error(f"Error dispatching event '{event_type}': {e}")


def _auto_read_message(c, message, source):
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


def _forward_to_handler(c, message):
    """Forward message to the callback handler."""
    try:
        from src.handlers.messageHandler import handleMessage
        asyncio.create_task(handleMessage(c, message))
    except Exception:
        pass


# ══════════════════════════════════════════════════════════
# CONTACT NAME RESOLVER
# ══════════════════════════════════════════════════════════

def get_contact_name(client, jid: str, push_name: str = None) -> str:
    """
    Resolve contact name with 4-level fallback:
    FullName > FirstName > BusinessName > PushName.
    """
    try:
        from neonize.utils import build_jid
        contact = client.contact_get(build_jid(jid))
        if contact:
            name = (
                contact.FullName
                or contact.FirstName
                or contact.BusinessName
                or contact.PushName
            )
            if name and name.strip():
                return name.strip()
    except Exception:
        pass
    return (push_name or "Anonymous").strip()


# ══════════════════════════════════════════════════════════
# EVENT HANDLERS (registered in start_bot)
# ══════════════════════════════════════════════════════════

def _build_qr_url() -> str:
    """Build the public /qr dashboard URL."""
    public_url = os.getenv("PUBLIC_URL")
    if not public_url:
        user = os.getenv("USER", "")
        if user:
            public_url = f"http://services-{user}.alwaysdata.net:{PORT}"
        else:
            hostname = socket.gethostname()
            public_url = f"http://{hostname}:{PORT}"
    else:
        if ":" not in public_url.split("/")[-1]:
            public_url = f"{public_url}:{PORT}"
    qr_url = f"{public_url}/qr"
    if API_KEY:
        qr_url += f"?API_KEY={API_KEY}"
    return qr_url


def _on_qr(c: NewClient, qr_bytes: bytes):
    global current_qr, qr_last_generated_at, _qr_url_logged

    # Always log the dashboard URL on the first QR event so the user knows where to go,
    # regardless of whether generation is active yet.
    if not _qr_url_logged:
        _qr_url_logged = True
        logger.info(f"📲 QR dashboard: {_build_qr_url()}")

    if not qr_generation_active:
        logger.debug("🔒 QR ignored — waiting for authenticated access on /qr")
        return

    current_qr = qr_bytes.decode("utf-8")
    qr_last_generated_at = time.time()
    logger.info(f"📲 QR Code ready! Access: {_build_qr_url()}")
    if main_loop and main_loop.is_running():
        main_loop.call_soon_threadsafe(
            lambda: asyncio.create_task(_fire("connection.qr_ready", {"qr": current_qr}))
        )


def _on_connected(c: NewClient, event: "ConnectedEv"):
    global is_ready, current_qr, current_pair_code, qr_generation_active, qr_last_generated_at, _qr_url_logged
    is_ready = True
    current_qr = None
    current_pair_code = None
    qr_generation_active = False
    qr_last_generated_at = None
    _qr_url_logged = False
    logger.info("✅ WhatsApp connected and ready")
    if main_loop and main_loop.is_running():
        phone = ""
        try:
            me = c.get_me()
            phone = me.JID.User
        except Exception:
            pass
        main_loop.call_soon_threadsafe(
            lambda: asyncio.create_task(_fire("connection.connected", {"phone": phone}))
        )


def _on_pair_code(c: NewClient, code: str, connected: bool):
    global current_pair_code
    if not connected:
        current_pair_code = code
        logger.info(f"🔑 Pairing code received: {code}")


def _on_history_sync(c: NewClient, event: "HistorySyncEv"):
    pass  # Skip history sync to conserve RAM


def _on_call_offer(c: NewClient, event: "CallOfferEv"):
    """Reject calls automatically if configured."""
    try:
        from src.services.whatsapp.settingsService import get_settings
        settings = get_settings()

        meta = event.basicCallMeta
        caller_jid = getattr(meta, "from")
        call_id = meta.callID

        from neonize.utils.jid import Jid2String
        caller_str = Jid2String(caller_jid)
        caller_phone = caller_str.split("@")[0]

        if main_loop and main_loop.is_running():
            main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(_fire("call.received", {
                    "from": caller_phone,
                    "fromJid": caller_str,
                    "callId": call_id,
                }))
            )

        if not settings.get("call_reject_auto", False):
            return

        logger.info(f"📞 Call from {caller_str} (ID: {call_id}) — rejecting automatically")

        msg = settings.get(
            "call_reject_message",
            "I'm not available right now. Please send a message.",
        )
        if msg and main_loop and main_loop.is_running():
            async def _send_call_reply():
                try:
                    c.send_message(caller_jid, msg)
                    logger.info(f"📞 Rejection message sent to {caller_str}")
                except Exception as send_err:
                    logger.warning(f"⚠️ Failed to send rejection message: {send_err}")

            main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(_send_call_reply())
            )
    except Exception as e:
        logger.error(f"Error in call handler: {e}")


def _on_message(c: NewClient, message: "MessageEv"):
    """Schedule received message processing in the main event loop."""
    if message.Info.Timestamp < START_TIME - 10:
        return
    try:
        if main_loop and main_loop.is_running():
            main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(handle_message_async(c, message))
            )
        else:
            logger.warning("🕒 Main loop not available to process message")
    except Exception as e:
        logger.error(f"Error scheduling message: {e}")


# ══════════════════════════════════════════════════════════
# MONKEY-PATCHES for Pair Code capture (fallback)
# ══════════════════════════════════════════════════════════

def _patch_neonize_logging():
    """
    Apply monkey-patches to capture pairing code that may come
    via CGo or Python logs, as fallback for the official paircode callback.
    """
    try:
        import neonize.utils as neonize_utils
        import neonize.client as neonize_client

        if hasattr(neonize_utils, "log_whatsmeow"):
            original_log_whatsmeow = neonize_utils.log_whatsmeow

            def patched_log_whatsmeow(binary, size):
                try:
                    from neonize.proto.Neonize_pb2 import LogEntry
                    import ctypes

                    log_msg = LogEntry.FromString(ctypes.string_at(binary, size))
                    _intercept_pair_code(log_msg.Message)
                except Exception:
                    pass
                return original_log_whatsmeow(binary, size)

            neonize_utils.log_whatsmeow = patched_log_whatsmeow
            neonize_client.log_whatsmeow = patched_log_whatsmeow
    except Exception as e:
        logger.warning(f"⚠️ Error patching log_whatsmeow: {e}")

    try:
        import neonize.events as neonize_events

        if not hasattr(neonize_events.log, "_patched"):
            original_events_info = neonize_events.log.info

            def patched_events_info(msg, *args, **kwargs):
                try:
                    full_msg = str(msg) % args if args else str(msg)
                    _intercept_pair_code(full_msg)
                except Exception:
                    pass
                return original_events_info(msg, *args, **kwargs)

            neonize_events.log.info = patched_events_info
            neonize_events.log._patched = True
    except Exception as e:
        logger.warning(f"⚠️ Error patching neonize.events: {e}")

    try:
        import builtins

        if not hasattr(builtins.print, "_patched"):
            original_print = builtins.print

            def patched_print(*args, **kwargs):
                try:
                    full_msg = " ".join(str(a) for a in args)
                    _intercept_pair_code(full_msg)
                except Exception:
                    pass
                return original_print(*args, **kwargs)

            builtins.print = patched_print
            builtins.print._patched = True
    except Exception as e:
        logger.warning(f"⚠️ Error patching builtins.print: {e}")


def _intercept_pair_code(text: str):
    """Try to extract a pairing code from a log string."""
    global current_pair_code
    if "Pair" in text or "code" in text.lower():
        match = re.search(r"([A-Z0-9]{4}[- ]?[A-Z0-9]{4})", text)
        if match:
            code = match.group(1).replace(" ", "-")
            current_pair_code = code
            logger.info(f"🎯 Code captured via interceptor: {code}")


# ══════════════════════════════════════════════════════════
# BOOTSTRAP: start_bot
# ══════════════════════════════════════════════════════════

async def start_bot():
    """Initialize the Neonize client: configure logging, register handlers and connect."""
    global client, is_ready, current_qr, main_loop
    main_loop = asyncio.get_running_loop()

    try:
        _reset_state()
        auth_file = str(Path(AUTH_DIR) / "auth.sqlite")
        _disconnect_existing()
        _configure_logging()
        _patch_neonize_logging()

        cleanup_db()
        client = NewClient(auth_file)
        _register_event_handlers()
        _load_db_config_and_start_scheduler()

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, client.connect)

    except Exception as e:
        logger.error(f"❌ Error starting bot: {str(e)}")
        await asyncio.sleep(RECONNECT_DELAY / 1000)
        asyncio.create_task(start_bot())


def _reset_state():
    """Reset global state variables for a new connection."""
    global qr_generation_active, qr_last_generated_at, current_qr, _keep_qr_active_on_restart, _qr_url_logged
    reset_pair_code()
    qr_last_generated_at = None
    current_qr = None
    _qr_url_logged = False
    if _keep_qr_active_on_restart:
        qr_generation_active = True
        _keep_qr_active_on_restart = False
    else:
        qr_generation_active = False


def _disconnect_existing():
    """Disconnect existing client if any."""
    global client
    if client:
        try:
            client.disconnect()
        except Exception:
            pass


def _configure_logging():
    """Configure Neonize log levels to reduce verbosity."""
    neonize_logger.setLevel(logging.ERROR)
    logging.getLogger("whatsmeow").setLevel(logging.INFO)


def _register_event_handlers():
    """Register all event callbacks on the Neonize client."""
    client.qr(_on_qr)
    client.event(ConnectedEv)(_on_connected)
    client.event.paircode(_on_pair_code)
    client.event(HistorySyncEv)(_on_history_sync)
    client.event(CallOfferEv)(_on_call_offer)
    client.event(MessageEv)(_on_message)


def _load_db_config_and_start_scheduler():
    """Load cleanup config and start the scheduler."""
    load_db_config()
    asyncio.create_task(db_cleanup_scheduler())


# ══════════════════════════════════════════════════════════
# LOGOUT
# ══════════════════════════════════════════════════════════

async def logout(keep_data=False):
    """Disconnect, clear session, and restart the bot."""
    global client, is_ready, current_qr
    logger.info(f"🗑️ Starting logout... (Keep data: {keep_data})")

    if client:
        try:
            client.logout()
            client.disconnect()
        except Exception:
            pass
        client = None

    is_ready = False
    current_qr = None

    if main_loop and main_loop.is_running():
        main_loop.call_soon_threadsafe(
            lambda: asyncio.create_task(_fire("connection.disconnected", {}))
        )

    auth_file = Path(AUTH_DIR) / "auth.sqlite"
    if auth_file.exists():
        try:
            auth_file.unlink()
        except Exception:
            pass

    if not keep_data:
        await storage.clear_all_data()
        logger.info("🧹 History data cleared.")

    logger.info("🔄 Restarting bot for new scan...")
    await asyncio.sleep(2)
    asyncio.create_task(start_bot())
