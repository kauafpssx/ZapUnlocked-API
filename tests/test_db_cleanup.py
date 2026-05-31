"""Tests for DB cleanup configuration persistence."""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.services.whatsapp.db_cleanup import (
    load_db_config,
    save_db_config,
    set_cleanup_interval,
    get_cleanup_state,
    cleanup_db,
)


@pytest.fixture(autouse=True)
def temp_db_config(tmp_path: Path):
    dummy_file = tmp_path / "db_config.json"
    dummy_file.parent.mkdir(parents=True, exist_ok=True)
    with patch("src.services.whatsapp.db_cleanup.DB_CONFIG_FILE", dummy_file):
        yield dummy_file


class TestLoadDbConfig:
    def test_defaults_when_no_file(self):
        load_db_config()
        state = get_cleanup_state()
        assert state["current_interval"] == 1440
        assert state["last_cleanup_time"] == 0

    def test_loads_existing_config(self, temp_db_config):
        temp_db_config.write_text('{"interval": 60, "last_run": 1000}')
        load_db_config()
        state = get_cleanup_state()
        assert state["current_interval"] == 60
        assert state["last_cleanup_time"] == 1000


class TestSetCleanupInterval:
    def test_updates_interval(self):
        set_cleanup_interval(30)
        state = get_cleanup_state()
        assert state["current_interval"] == 30


class TestSaveDbConfig:
    def test_persists_to_disk(self, temp_db_config):
        set_cleanup_interval(120)
        content = temp_db_config.read_text()
        assert '"interval": 120' in content

    def test_get_cleanup_state_returns_dict(self):
        state = get_cleanup_state()
        assert "last_cleanup_time" in state
        assert "current_interval" in state


class TestCleanupDb:
    @patch("src.services.whatsapp.state.get_cleanup_lock")
    def test_skips_when_lock_unavailable(self, mock_get_lock):
        mock_lock = unittest.mock.MagicMock()
        mock_lock.acquire.return_value = False
        mock_get_lock.return_value = mock_lock

        cleanup_db()
        mock_lock.acquire.assert_called_once_with(blocking=False)


import unittest.mock
