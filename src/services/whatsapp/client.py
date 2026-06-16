"""
WhatsApp client lifecycle — connection, monkey-patches, and logout.

State lives in state.py (accessed via functional API),
DB cleanup in db_cleanup.py,
and event handlers in event_handlers.py.
"""

import asyncio
import logging
import re
import sys
from pathlib import Path

from neonize.client import NewClient
from neonize.events import (
    ConnectedEv, MessageEv, HistorySyncEv, CallOfferEv,
    LoggedOutEv, ConnectFailureEv, StreamErrorEv,
    TemporaryBanEv, ClientOutdatedEv, StreamReplacedEv,
    PairStatusEv, JoinedGroupEv, GroupInfoEv,
    PresenceEv, ChatPresenceEv, PictureEv, IdentityChangeEv,
    ReceiptEv, CallAcceptEv, CallTerminateEv,
    UndecryptableMessageEv,
)
from neonize.utils import log as neonize_logger

from src.utils.logger import logger
from src.config.constants import RECONNECT_DELAY, get_auth_dir

from src.services.whatsapp import state

# Re-export state getters so `from client import get_is_ready` still works
from src.services.whatsapp.state import (
    get_client, get_is_ready, get_qr, get_reaction_cache,
    get_qr_expires_in,
)

from src.services.whatsapp.db_cleanup import (
    load_db_config, save_db_config, cleanup_db, db_cleanup_scheduler,
    set_cleanup_interval, get_cleanup_state,
)

from src.services.whatsapp.event_handlers import (
    _on_qr, _on_connected, _on_pair_code,
    _on_history_sync, _on_call_offer, _on_message,
    _on_logged_out, _on_connect_failure, _on_stream_error,
    _on_temporary_ban, _on_client_outdated, _on_stream_replaced,
    _on_pair_status, _on_joined_group, _on_group_info,
    _on_presence, _on_chat_presence, _on_picture, _on_identity_change,
    _on_receipt, _on_call_accept, _on_call_terminate,
    _on_undecryptable,
    handle_message_async,
)


_shutting_down = False
_reconnect_attempts: dict[str, int] = {}


def set_shutting_down(value: bool) -> None:
    global _shutting_down
    _shutting_down = value


def is_shutting_down() -> bool:
    return _shutting_down


def reset_reconnect_counter(session_id: str) -> None:
    _reconnect_attempts.pop(session_id, None)


# ═══════════════════════════════════════════════════════════════════════════
# QR ACTIVATION
# ═══════════════════════════════════════════════════════════════════════════

def activate_qr(session_id: str | None = None) -> None:
    """Authorize QR storage after valid /qr or /qr/image access.
    No-op if already connected. Restarts bot if QR has expired."""
    if state.get_is_ready(session_id) or _shutting_down:
        return
    state.set_qr_generation_active(True, session_id)
    if state.get_qr(session_id) is None and state.get_main_loop(session_id) and state.get_main_loop(session_id).is_running():
        state.set_keep_qr_active_on_restart(True, session_id)
        _sid = session_id
        state.get_main_loop(session_id).call_soon_threadsafe(
            lambda: asyncio.create_task(start_bot(_sid))
        )


# ═══════════════════════════════════════════════════════════════════════════
# PAIR CODE INTERCEPTOR
# ═══════════════════════════════════════════════════════════════════════════

def _intercept_pair_code(text: str) -> None:
    """Try to extract a pairing code from a log string."""
    if "Pair" in text or "code" in text.lower():
        match = re.search(r"([A-Z0-9]{4}[- ]?[A-Z0-9]{4})", text)
        if match:
            code = match.group(1).replace(" ", "-")
            state.set_current_pair_code(code)
            logger.info(f"🎯 Code captured via interceptor: {code}")


# ═══════════════════════════════════════════════════════════════════════════
# MONKEY-PATCHES (fallback pair-code capture)
# These exist because Neonize's official paircode callback sometimes does
# not fire.  Isolated here so they can be easily removed once the upstream
# library is fixed.
# ═══════════════════════════════════════════════════════════════════════════

def _patch_neonize_logging() -> None:
    """Patch neonize internals to capture pairing codes as a fallback."""
    # Patch 1: neonize.utils.log_whatsmeow (C FFI log callback)
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

    # Patch 2: neonize.events logger
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

    # Patch 3: sys.stdout (replaces the previous builtins.print override)
    # print() calls sys.stdout.write() internally.
    try:
        class _PairCodeStdout:
            def __init__(self, wrapped):
                self._wrapped = wrapped

            def write(self, text):
                try:
                    _intercept_pair_code(str(text))
                except Exception:
                    pass
                return self._wrapped.write(text)

            def flush(self):
                return self._wrapped.flush()

            def __getattr__(self, name):
                return getattr(self._wrapped, name)

        if not isinstance(sys.stdout, _PairCodeStdout):
            sys.stdout = _PairCodeStdout(sys.stdout)
    except Exception as e:
        logger.warning(f"⚠️ Error patching sys.stdout: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# BOOTSTRAP
# ═══════════════════════════════════════════════════════════════════════════

async def start_bot(session_id: str | None = None) -> None:
    """Initialize the Neonize client for session_id."""
    if _shutting_down:
        return

    from src.services.sessions.registry import get_default_session_id
    sid = session_id or get_default_session_id()

    state.set_main_loop(asyncio.get_running_loop(), sid)

    try:
        _reset_state(sid)
        auth_file = str(Path(get_auth_dir(sid)) / "auth.sqlite")
        Path(auth_file).parent.mkdir(parents=True, exist_ok=True)
        _disconnect_existing(sid)
        _configure_logging()
        _patch_neonize_logging()

        cleanup_db(sid)
        client = NewClient(auth_file)
        state.set_client(client, sid)
        _register_event_handlers(sid)
        _load_db_config_and_start_scheduler(sid)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, state.get_client(sid).connect)

    except Exception as e:
        if _shutting_down:
            return
        attempts = _reconnect_attempts.get(sid, 0)
        delay = min((RECONNECT_DELAY / 1000) * (2 ** attempts), 300)
        _reconnect_attempts[sid] = attempts + 1
        logger.error(f"❌ Error starting bot (session={sid}): {e} — retry in {delay:.0f}s (attempt {attempts + 1})")
        await asyncio.sleep(delay)
        asyncio.create_task(start_bot(sid))


def _reset_state(session_id: str | None = None) -> None:
    state.reset_for_reconnect(session_id)


def _disconnect_existing(session_id: str | None = None) -> None:
    """Disconnect existing client if any."""
    client = state.get_client(session_id)
    if client:
        try:
            client.disconnect()
        except Exception:
            pass


def _configure_logging() -> None:
    """Configure Neonize log levels to reduce verbosity."""
    neonize_logger.setLevel(logging.ERROR)
    logging.getLogger("whatsmeow").setLevel(logging.INFO)


def _register_event_handlers(session_id: str | None = None) -> None:
    """Register all event callbacks on the Neonize client."""
    from src.services.whatsapp.event_handlers import register_client_session
    client = state.get_client(session_id)
    if not client:
        logger.error("Cannot register event handlers: client is None")
        return

    register_client_session(client, session_id or "1")

    client.qr(_on_qr)
    client.event.paircode(_on_pair_code)

    # ── Connection lifecycle ───────────────────────────────
    client.event(ConnectedEv)(_on_connected)
    client.event(HistorySyncEv)(_on_history_sync)
    client.event(LoggedOutEv)(_on_logged_out)
    client.event(ConnectFailureEv)(_on_connect_failure)
    client.event(StreamErrorEv)(_on_stream_error)
    client.event(TemporaryBanEv)(_on_temporary_ban)
    client.event(ClientOutdatedEv)(_on_client_outdated)
    client.event(StreamReplacedEv)(_on_stream_replaced)
    client.event(PairStatusEv)(_on_pair_status)

    # ── Messages ───────────────────────────────────────────
    client.event(MessageEv)(_on_message)
    client.event(UndecryptableMessageEv)(_on_undecryptable)

    # ── Receipts ───────────────────────────────────────────
    client.event(ReceiptEv)(_on_receipt)

    # ── Groups ─────────────────────────────────────────────
    client.event(JoinedGroupEv)(_on_joined_group)
    client.event(GroupInfoEv)(_on_group_info)

    # ── Contact / Presence ─────────────────────────────────
    client.event(PresenceEv)(_on_presence)
    client.event(ChatPresenceEv)(_on_chat_presence)
    client.event(PictureEv)(_on_picture)
    client.event(IdentityChangeEv)(_on_identity_change)

    # ── Calls ──────────────────────────────────────────────
    client.event(CallOfferEv)(_on_call_offer)
    client.event(CallAcceptEv)(_on_call_accept)
    client.event(CallTerminateEv)(_on_call_terminate)


def _load_db_config_and_start_scheduler(session_id: str | None = None) -> None:
    load_db_config(session_id)
    asyncio.create_task(db_cleanup_scheduler(session_id))


# ═══════════════════════════════════════════════════════════════════════════
# LOGOUT
# ═══════════════════════════════════════════════════════════════════════════

async def logout(keep_data: bool = False, session_id: str | None = None) -> None:
    """Disconnect, clear session, and restart the bot."""
    from src.services.whatsapp import storage
    from src.services.whatsapp.event_handlers import _fire
    from src.services.sessions.registry import get_default_session_id

    sid = session_id or get_default_session_id()
    logger.info(f"🗑️ Starting logout (session={sid}, keep_data={keep_data})...")

    client = state.get_client(sid)
    if client:
        try:
            client.logout()
            client.disconnect()
        except Exception:
            pass

    state.reset_for_logout(sid)

    loop = state.get_main_loop(sid)
    if loop and loop.is_running():
        loop.call_soon_threadsafe(
            lambda: asyncio.create_task(_fire("connection.disconnected", {}, sid))
        )

    auth_file = Path(get_auth_dir(sid)) / "auth.sqlite"
    if auth_file.exists():
        try:
            auth_file.unlink()
        except Exception:
            pass

    if not keep_data:
        await storage.clear_all_data(sid)
        logger.info("🧹 History data cleared.")

    logger.info("🔄 Restarting bot for new scan...")
    await asyncio.sleep(2)
    asyncio.create_task(start_bot(sid))
