"""
WhatsAppState — thread-safe singleton for WhatsApp client connection state.

Encapsulates all module-level variables in a single class with explicit
getters/setters so the state is testable, mockable, and safe from
import-order bugs.

Usage:
    from src.services.whatsapp.state_manager import WhatsAppState
    state = WhatsAppState()
    state.is_ready = True
"""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from neonize.client import NewClient


_states: dict[str, "WhatsAppState"] = {}
_states_lock: threading.Lock = threading.Lock()


def get_state(session_id: str) -> "WhatsAppState":
    """Return existing state for session_id, creating it if needed."""
    with _states_lock:
        if session_id not in _states:
            _states[session_id] = WhatsAppState.__new__(WhatsAppState)
            _states[session_id]._initialized = False
            _states[session_id].__init__()
        return _states[session_id]


def create_state(session_id: str) -> "WhatsAppState":
    """Create (or reset) state for session_id."""
    with _states_lock:
        st = WhatsAppState.__new__(WhatsAppState)
        st._initialized = False
        st.__init__()
        _states[session_id] = st
        return st


def remove_state(session_id: str) -> None:
    with _states_lock:
        _states.pop(session_id, None)


def all_states() -> dict[str, "WhatsAppState"]:
    with _states_lock:
        return dict(_states)


class WhatsAppState:
    """Per-session WhatsApp client connection state (no longer a singleton)."""

    def __new__(cls) -> "WhatsAppState":
        return super().__new__(cls)

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._reset()

    # ── Reset ──────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset all state to defaults — useful for testing."""
        self._reset()

    def _reset(self) -> None:
        """Reset all state to defaults — useful for testing and reconnection."""
        self._client: Optional[NewClient] = None
        self._is_ready: bool = False
        self._current_qr: Optional[str] = None
        self._current_pair_code: Optional[str] = None
        self._reaction_cache: dict = {}
        self._start_time: float = time.time()
        self._connected_at: Optional[float] = None
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None

        # QR gating — only store QR after an authenticated request
        self._qr_generation_active: bool = False
        self._qr_last_generated_at: Optional[float] = None
        self._qr_expiry_seconds: int = 60
        self._keep_qr_active_on_restart: bool = False
        self._qr_url_logged: bool = False

        # Misc
        self._max_reactions_in_cache: int = 1000
        self._cleanup_lock: threading.Lock = threading.Lock()

    def reset_for_reconnect(self) -> None:
        """Soft reset that preserves _keep_qr_active_on_restart flag."""
        self._current_pair_code = None
        self._qr_last_generated_at = None
        self._current_qr = None
        self._qr_url_logged = False
        if self._keep_qr_active_on_restart:
            self._qr_generation_active = True
            self._keep_qr_active_on_restart = False
        else:
            self._qr_generation_active = False

    def reset_for_logout(self) -> None:
        """Reset state after a logout."""
        self._client = None
        self._is_ready = False
        self._current_qr = None
        self._main_loop = None

    # ── Client ─────────────────────────────────────────────────────────────

    @property
    def client(self) -> Optional[NewClient]:
        return self._client

    @client.setter
    def client(self, value: Optional[NewClient]) -> None:
        self._client = value

    # ── Connection readiness ───────────────────────────────────────────────

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    @is_ready.setter
    def is_ready(self, value: bool) -> None:
        self._is_ready = value

    # ── QR code ────────────────────────────────────────────────────────────

    @property
    def current_qr(self) -> Optional[str]:
        return self._current_qr

    @current_qr.setter
    def current_qr(self, value: Optional[str]) -> None:
        self._current_qr = value

    # ── Pair code ──────────────────────────────────────────────────────────

    @property
    def current_pair_code(self) -> Optional[str]:
        return self._current_pair_code

    @current_pair_code.setter
    def current_pair_code(self, value: Optional[str]) -> None:
        self._current_pair_code = value

    # ── Reaction cache ─────────────────────────────────────────────────────

    @property
    def reaction_cache(self) -> dict:
        return self._reaction_cache

    @reaction_cache.setter
    def reaction_cache(self, value: dict) -> None:
        self._reaction_cache = value

    # ── Start time ─────────────────────────────────────────────────────────

    @property
    def start_time(self) -> float:
        return self._start_time

    # ── Connected at ───────────────────────────────────────────────────────

    @property
    def connected_at(self) -> Optional[float]:
        return self._connected_at

    @connected_at.setter
    def connected_at(self, value: Optional[float]) -> None:
        self._connected_at = value

    # ── Event loop ─────────────────────────────────────────────────────────

    @property
    def main_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        return self._main_loop

    @main_loop.setter
    def main_loop(self, value: Optional[asyncio.AbstractEventLoop]) -> None:
        self._main_loop = value

    # ── QR gating ──────────────────────────────────────────────────────────

    @property
    def qr_generation_active(self) -> bool:
        return self._qr_generation_active

    @qr_generation_active.setter
    def qr_generation_active(self, value: bool) -> None:
        self._qr_generation_active = value

    @property
    def qr_last_generated_at(self) -> Optional[float]:
        return self._qr_last_generated_at

    @qr_last_generated_at.setter
    def qr_last_generated_at(self, value: Optional[float]) -> None:
        self._qr_last_generated_at = value

    @property
    def qr_expiry_seconds(self) -> int:
        return self._qr_expiry_seconds

    @property
    def keep_qr_active_on_restart(self) -> bool:
        return self._keep_qr_active_on_restart

    @keep_qr_active_on_restart.setter
    def keep_qr_active_on_restart(self, value: bool) -> None:
        self._keep_qr_active_on_restart = value

    @property
    def qr_url_logged(self) -> bool:
        return self._qr_url_logged

    @qr_url_logged.setter
    def qr_url_logged(self, value: bool) -> None:
        self._qr_url_logged = value

    # ── Misc ───────────────────────────────────────────────────────────────

    @property
    def max_reactions_in_cache(self) -> int:
        return self._max_reactions_in_cache

    @property
    def cleanup_lock(self) -> threading.Lock:
        return self._cleanup_lock

    # ── Derived helpers ────────────────────────────────────────────────────

    def get_qr_expires_in(self) -> Optional[int]:
        """Remaining seconds of the current QR. None if no QR."""
        if self._current_qr is None or self._qr_last_generated_at is None:
            return None
        remaining = self._qr_expiry_seconds - int(time.time() - self._qr_last_generated_at)
        return max(remaining, 0)


# ═══════════════════════════════════════════════════════════════════════════
# Functional API (previously in state.py)
# ═══════════════════════════════════════════════════════════════════════════

def _default_session_id() -> str:
    from src.services.sessions.registry import get_default_session_id
    return get_default_session_id()


def _s(session_id: str | None) -> WhatsAppState:
    sid = session_id if session_id is not None else _default_session_id()
    return get_state(sid)


def get_client(session_id: str | None = None) -> Optional["NewClient"]:
    return _s(session_id).client


def get_is_ready(session_id: str | None = None) -> bool:
    return _s(session_id).is_ready


def get_qr(session_id: str | None = None) -> Optional[str]:
    return _s(session_id).current_qr


def get_reaction_cache(session_id: str | None = None) -> dict:
    return _s(session_id).reaction_cache


def get_main_loop(session_id: str | None = None) -> Optional[asyncio.AbstractEventLoop]:
    return _s(session_id).main_loop


def get_qr_generation_active(session_id: str | None = None) -> bool:
    return _s(session_id).qr_generation_active


def get_qr_last_generated_at(session_id: str | None = None) -> Optional[float]:
    return _s(session_id).qr_last_generated_at


def get_qr_url_logged(session_id: str | None = None) -> bool:
    return _s(session_id).qr_url_logged


def get_keep_qr_active_on_restart(session_id: str | None = None) -> bool:
    return _s(session_id).keep_qr_active_on_restart


def get_qr_expires_in(session_id: str | None = None) -> Optional[int]:
    return _s(session_id).get_qr_expires_in()


def get_start_time(session_id: str | None = None) -> float:
    return _s(session_id).start_time


def get_connected_at(session_id: str | None = None) -> Optional[float]:
    return _s(session_id).connected_at


def get_cleanup_lock(session_id: str | None = None) -> threading.Lock:
    return _s(session_id).cleanup_lock


def set_client(value, session_id: str | None = None) -> None:
    _s(session_id).client = value


def set_is_ready(value: bool, session_id: str | None = None) -> None:
    _s(session_id).is_ready = value


def set_current_qr(value: Optional[str], session_id: str | None = None) -> None:
    _s(session_id).current_qr = value


def set_current_pair_code(value: Optional[str], session_id: str | None = None) -> None:
    _s(session_id).current_pair_code = value


def set_main_loop(value: Optional[asyncio.AbstractEventLoop], session_id: str | None = None) -> None:
    _s(session_id).main_loop = value


def set_qr_generation_active(value: bool, session_id: str | None = None) -> None:
    _s(session_id).qr_generation_active = value


def set_qr_last_generated_at(value: Optional[float], session_id: str | None = None) -> None:
    _s(session_id).qr_last_generated_at = value


def set_qr_url_logged(value: bool, session_id: str | None = None) -> None:
    _s(session_id).qr_url_logged = value


def set_keep_qr_active_on_restart(value: bool, session_id: str | None = None) -> None:
    _s(session_id).keep_qr_active_on_restart = value


def set_connected_at(value: Optional[float], session_id: str | None = None) -> None:
    _s(session_id).connected_at = value


def mark_connected(session_id: str | None = None) -> None:
    st = _s(session_id)
    st.is_ready = True
    st.connected_at = time.time()
    st.current_qr = None
    st.current_pair_code = None
    st.qr_generation_active = False
    st.qr_last_generated_at = None
    st.qr_url_logged = False


def mark_disconnected(session_id: str | None = None) -> None:
    st = _s(session_id)
    st.is_ready = False
    st.current_qr = None


def reset_for_reconnect(session_id: str | None = None) -> None:
    _s(session_id).reset_for_reconnect()


def reset_for_logout(session_id: str | None = None) -> None:
    _s(session_id).reset_for_logout()
