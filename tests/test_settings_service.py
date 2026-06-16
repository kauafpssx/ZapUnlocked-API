"""Tests for the WhatsApp settings service (SQLite-backed)."""

import pytest

from src.services.whatsapp.settingsService import get_settings, save_settings, DEFAULT_SETTINGS


@pytest.fixture(autouse=True)
def use_temp_db(temp_db):
    pass


class TestGetSettings:
    def test_returns_defaults_when_no_file(self):
        settings = get_settings()
        assert settings["ip_control_enabled"] is False
        assert settings["auto_read_message"] is False

    def test_merges_stored_key_with_defaults(self):
        save_settings({"ip_control_enabled": True})
        settings = get_settings()
        assert settings["ip_control_enabled"] is True
        assert settings["auto_read_message"] is False


class TestSaveSettings:
    def test_saves_and_returns_merged(self):
        result = save_settings({"ip_control_enabled": True})
        assert result["ip_control_enabled"] is True
        settings = get_settings()
        assert settings["ip_control_enabled"] is True

    def test_preserves_other_keys(self):
        save_settings({"ip_control_enabled": True})
        save_settings({"auto_read_message": True})
        settings = get_settings()
        assert settings["ip_control_enabled"] is True
        assert settings["auto_read_message"] is True

    def test_session_isolation(self):
        save_settings({"ip_control_enabled": True}, session_id="1")
        settings_2 = get_settings(session_id="2")
        assert settings_2["ip_control_enabled"] is False
