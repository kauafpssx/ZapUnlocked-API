"""Tests for the state module's functional API (getters/setters)."""

import pytest

from src.services.whatsapp import state


class TestStateGettersSetters:
    """Test that getter/setter functions work correctly."""

    def test_is_ready_cycle(self):
        state.set_is_ready(True)
        assert state.get_is_ready() is True
        state.set_is_ready(False)
        assert state.get_is_ready() is False

    def test_qr_cycle(self):
        state.set_current_qr("test_qr")
        assert state.get_qr() == "test_qr"
        state.set_current_qr(None)
        assert state.get_qr() is None

    def test_main_loop_cycle(self):
        assert state.get_main_loop() is None

    def test_qr_generation_active(self):
        assert state.get_qr_generation_active() is False
        state.set_qr_generation_active(True)
        assert state.get_qr_generation_active() is True
        state.set_qr_generation_active(False)

    def test_qr_url_logged(self):
        state.set_qr_url_logged(True)
        assert state.get_qr_url_logged() is True
        state.set_qr_url_logged(False)
        assert state.get_qr_url_logged() is False

    def test_qr_last_generated_at(self):
        import time
        now = time.time()
        state.set_qr_last_generated_at(now)
        assert state.get_qr_last_generated_at() == now
        state.set_qr_last_generated_at(None)
        assert state.get_qr_last_generated_at() is None

    def test_keep_qr_active_on_restart(self):
        state.set_keep_qr_active_on_restart(True)
        assert state.get_keep_qr_active_on_restart() is True
        state.set_keep_qr_active_on_restart(False)

    def test_qr_expires_in_function(self):
        import time
        state.set_current_qr("test")
        state.set_qr_last_generated_at(time.time())
        result = state.get_qr_expires_in()
        assert result is not None
        assert 0 <= result <= 60
        state.set_current_qr(None)
        state.set_qr_last_generated_at(None)


class TestStateCompoundHelpers:
    """Test compound helpers like mark_connected and reset_for_reconnect."""

    def test_mark_connected(self):
        state.set_current_qr("test")
        state.set_current_pair_code("ABCD")
        state.set_qr_generation_active(True)

        state.mark_connected()

        assert state.get_is_ready() is True
        assert state.get_qr() is None
        assert state.get_qr_generation_active() is False

    def test_mark_disconnected(self):
        state.set_is_ready(True)
        state.set_current_qr("test")

        state.mark_disconnected()

        assert state.get_is_ready() is False
        assert state.get_qr() is None

    def test_reset_for_reconnect(self):
        """reset_for_reconnect should preserve keep_qr_active."""
        state.set_current_pair_code("ABCD")
        state.set_keep_qr_active_on_restart(True)
        state.set_current_qr("qr")

        state.reset_for_reconnect()

        assert state.get_qr() is None
        # keep_qr_active should have been consumed
        assert state.get_qr_generation_active() is True
