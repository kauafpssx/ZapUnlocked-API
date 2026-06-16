"""Tests for DB cleanup configuration persistence (SQLite-backed)."""

import unittest.mock

import pytest

from src.services.whatsapp.db_cleanup import (
    load_db_config,
    save_db_config,
    set_cleanup_interval,
    get_cleanup_state,
    cleanup_db,
    _session_config,
)


@pytest.fixture(autouse=True)
def use_temp_db(temp_db):
    # Also clear in-memory cache between tests
    _session_config.clear()
    yield
    _session_config.clear()


class TestLoadDbConfig:
    def test_defaults_when_no_row(self):
        load_db_config()
        state = get_cleanup_state()
        assert state["current_interval"] == 1440
        assert state["last_cleanup_time"] == 0

    def test_loads_existing_config(self):
        from src.utils.db import get_conn
        conn = get_conn()
        conn.execute(
            "INSERT INTO db_config (session_id, interval, last_run) VALUES ('1', 60, 1000)"
        )
        conn.commit()
        load_db_config()
        state = get_cleanup_state()
        assert state["current_interval"] == 60
        assert state["last_cleanup_time"] == 1000


class TestSetCleanupInterval:
    def test_updates_interval(self):
        set_cleanup_interval(30)
        state = get_cleanup_state()
        assert state["current_interval"] == 30

    def test_persists_to_db(self):
        set_cleanup_interval(120)
        _session_config.clear()  # evict in-memory cache
        load_db_config()
        state = get_cleanup_state()
        assert state["current_interval"] == 120


class TestGetCleanupState:
    def test_returns_expected_keys(self):
        state = get_cleanup_state()
        assert "last_cleanup_time" in state
        assert "current_interval" in state


class TestCleanupDb:
    @unittest.mock.patch("src.services.whatsapp.state.get_cleanup_lock")
    def test_skips_when_lock_unavailable(self, mock_get_lock):
        mock_lock = unittest.mock.MagicMock()
        mock_lock.acquire.return_value = False
        mock_get_lock.return_value = mock_lock

        cleanup_db()
        mock_lock.acquire.assert_called_once_with(blocking=False)
