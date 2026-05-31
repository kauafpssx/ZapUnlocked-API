"""
WhatsApp client state — thread-safe singleton with functional API.

All state lives inside a WhatsAppState singleton. Access it through
the getter/setter functions below — never through direct attribute
access on the module.

Why functions instead of module-level variables?
  - Testability: tests can reset state between runs
  - Safety: no import-order bugs from mutable module globals
  - Traceability: setters are easy to instrument/log
  - DI: WhatsAppState can be injected in tests

Usage:
    from src.services.whatsapp import state
    state.get_is_ready()
    state.set_is_ready(True)
"""

from __future__ import annotations

import asyncio
import threading
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from neonize.client import NewClient

from src.services.whatsapp.state_manager import WhatsAppState

# ── Singleton backend ──────────────────────────────────────────────────────
_state = WhatsAppState()

# ═══════════════════════════════════════════════════════════════════════════
# GETTERS
# ═══════════════════════════════════════════════════════════════════════════

def get_client() -> Optional[NewClient]:
    return _state.client


def get_is_ready() -> bool:
    return _state.is_ready


def get_qr() -> Optional[str]:
    return _state.current_qr


def get_reaction_cache() -> dict:
    return _state.reaction_cache


def get_main_loop() -> Optional[asyncio.AbstractEventLoop]:
    return _state.main_loop


def get_qr_generation_active() -> bool:
    return _state.qr_generation_active


def get_qr_last_generated_at() -> Optional[float]:
    return _state.qr_last_generated_at


def get_qr_url_logged() -> bool:
    return _state.qr_url_logged


def get_keep_qr_active_on_restart() -> bool:
    return _state.keep_qr_active_on_restart


def get_qr_expires_in() -> Optional[int]:
    """Remaining seconds of the current QR. None if no QR."""
    return _state.get_qr_expires_in()


# ═══════════════════════════════════════════════════════════════════════════
# SETTERS
# ═══════════════════════════════════════════════════════════════════════════

def set_client(value: Optional[NewClient]) -> None:
    _state.client = value


def set_is_ready(value: bool) -> None:
    _state.is_ready = value


def set_current_qr(value: Optional[str]) -> None:
    _state.current_qr = value


def set_current_pair_code(value: Optional[str]) -> None:
    _state.current_pair_code = value


def set_main_loop(value: Optional[asyncio.AbstractEventLoop]) -> None:
    _state.main_loop = value


def set_qr_generation_active(value: bool) -> None:
    _state.qr_generation_active = value


def set_qr_last_generated_at(value: Optional[float]) -> None:
    _state.qr_last_generated_at = value


def set_qr_url_logged(value: bool) -> None:
    _state.qr_url_logged = value


def set_keep_qr_active_on_restart(value: bool) -> None:
    _state.keep_qr_active_on_restart = value


# ═══════════════════════════════════════════════════════════════════════════
# COMPOUND HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def mark_connected() -> None:
    """Set all state vars to 'connected'."""
    _state.is_ready = True
    _state.current_qr = None
    _state.current_pair_code = None
    _state.qr_generation_active = False
    _state.qr_last_generated_at = None
    _state.qr_url_logged = False


def mark_disconnected() -> None:
    """Set all state vars to 'disconnected'."""
    _state.is_ready = False
    _state.current_qr = None


def reset_for_reconnect() -> None:
    """Soft reset — preserves _keep_qr_active_on_restart for auto-restart."""
    _state.reset_for_reconnect()


def reset_for_logout() -> None:
    """Hard reset after a full logout."""
    _state.reset_for_logout()


def get_start_time() -> float:
    return _state.start_time


def get_cleanup_lock() -> threading.Lock:
    """Return the cleanup thread lock (for db_cleanup coordination)."""
    return _state.cleanup_lock
