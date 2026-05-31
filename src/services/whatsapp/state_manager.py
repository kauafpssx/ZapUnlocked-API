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


class WhatsAppState:
    """Thread-safe singleton holding all WhatsApp client connection state."""

    _instance: Optional["WhatsAppState"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "WhatsAppState":
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
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
