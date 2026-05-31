"""Tests for the WhatsAppState singleton class."""

import asyncio
import time
import threading
from unittest.mock import MagicMock

import pytest

from src.services.whatsapp.state_manager import WhatsAppState


@pytest.fixture(autouse=True)
def reset_state():
    """Reset the singleton state before and after each test."""
    state = WhatsAppState()
    state.reset()
    yield
    state.reset()


class TestWhatsAppStateSingleton:
    """Verify singleton behavior."""

    def test_same_instance(self):
        """Multiple instantiations return the same object."""
        s1 = WhatsAppState()
        s2 = WhatsAppState()
        assert s1 is s2

    def test_reset_clears_all_state(self):
        """reset() should clear all state."""
        state = WhatsAppState()
        state.client = MagicMock()
        state.is_ready = True
        state.current_qr = "qr_data_here"
        state.current_pair_code = "ABCD-1234"

        state.reset()

        assert state.client is None
        assert state.is_ready is False
        assert state.current_qr is None
        assert state.current_pair_code is None
        assert state.qr_last_generated_at is None
        assert state.qr_url_logged is False

    def test_reset_for_reconnect_preserves_is_ready(self):
        """reset_for_reconnect does not clear is_ready."""
        state = WhatsAppState()
        state.is_ready = True
        state.current_qr = "qr"
        state.current_pair_code = "ABCD"

        state.reset_for_reconnect()

        assert state.current_pair_code is None
        assert state.current_qr is None
        # is_ready is NOT cleared by reset_for_reconnect
        assert state.is_ready is True


class TestWhatsAppStateProperties:
    """Test getter/setter properties."""

    def test_client_property(self):
        state = WhatsAppState()
        mock = MagicMock()
        state.client = mock
        assert state.client is mock

    def test_is_ready_property(self):
        state = WhatsAppState()
        assert state.is_ready is False
        state.is_ready = True
        assert state.is_ready is True
        state.is_ready = False
        assert state.is_ready is False

    def test_current_qr_property(self):
        state = WhatsAppState()
        assert state.current_qr is None
        state.current_qr = "test_qr"
        assert state.current_qr == "test_qr"

    def test_current_pair_code(self):
        state = WhatsAppState()
        assert state.current_pair_code is None
        state.current_pair_code = "ABCD-1234"
        assert state.current_pair_code == "ABCD-1234"

    def test_reaction_cache(self):
        state = WhatsAppState()
        assert state.reaction_cache == {}
        state.reaction_cache["key"] = "value"
        assert state.reaction_cache["key"] == "value"

    def test_main_loop(self):
        state = WhatsAppState()
        assert state.main_loop is None
        loop = asyncio.new_event_loop()
        state.main_loop = loop
        assert state.main_loop is loop
        loop.close()

    def test_start_time_is_set(self):
        state = WhatsAppState()
        assert state.start_time > 0
        assert abs(state.start_time - time.time()) < 2

    def test_qr_expiry_defaults(self):
        state = WhatsAppState()
        assert state.qr_expiry_seconds == 60
        assert state.qr_generation_active is False

    def test_cleanup_lock_is_lock(self):
        state = WhatsAppState()
        assert isinstance(state.cleanup_lock, type(threading.Lock()))


class TestWhatsAppStateQRHelpers:
    """Test QR and pair code related functionality."""

    def test_get_qr_expires_in_no_qr(self):
        state = WhatsAppState()
        assert state.get_qr_expires_in() is None

    def test_get_qr_expires_in_with_qr(self):
        state = WhatsAppState()
        state.current_qr = "test_qr"
        state.qr_last_generated_at = time.time()
        result = state.get_qr_expires_in()
        assert result is not None
        assert 0 <= result <= 60

    def test_get_qr_expires_in_expired(self):
        state = WhatsAppState()
        state.current_qr = "test_qr"
        state.qr_last_generated_at = time.time() - 120  # 2 min ago
        result = state.get_qr_expires_in()
        assert result == 0

    def test_reset_for_logout(self):
        state = WhatsAppState()
        state.client = MagicMock()
        state.is_ready = True
        state.current_qr = "qr_data"

        state.reset_for_logout()

        assert state.client is None
        assert state.is_ready is False
        assert state.current_qr is None
