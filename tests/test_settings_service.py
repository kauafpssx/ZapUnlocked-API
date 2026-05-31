"""Tests for the WhatsApp settings service (file-based)."""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.services.whatsapp.settingsService import get_settings, save_settings


@pytest.fixture(autouse=True)
def temp_settings_file(tmp_path: Path):
    dummy_file = tmp_path / "settings.json"
    dummy_file.parent.mkdir(parents=True, exist_ok=True)
    with patch("src.services.whatsapp.settingsService.SETTINGS_FILE", dummy_file):
        yield dummy_file


class TestGetSettings:
    def test_returns_defaults_when_no_file(self):
        settings = get_settings()
        assert settings["ai_tag_enabled"] is False
        assert settings["ip_control_enabled"] is False
        assert settings["auto_read_message"] is False

    def test_merges_with_defaults_for_missing_keys(self, temp_settings_file):
        temp_settings_file.write_text('{"ai_tag_enabled": true}')
        settings = get_settings()
        assert settings["ai_tag_enabled"] is True
        assert settings["ip_control_enabled"] is False

    def test_returns_defaults_on_corrupt_file(self, temp_settings_file):
        temp_settings_file.write_text("not json")
        settings = get_settings()
        assert settings["ai_tag_enabled"] is False


class TestSaveSettings:
    def test_saves_and_returns_merged(self, temp_settings_file):
        result = save_settings({"ai_tag_enabled": True})
        assert result["ai_tag_enabled"] is True
        settings = get_settings()
        assert settings["ai_tag_enabled"] is True

    def test_preserves_other_keys(self, temp_settings_file):
        save_settings({"ai_tag_enabled": True})
        save_settings({"auto_read_message": True})
        settings = get_settings()
        assert settings["ai_tag_enabled"] is True
        assert settings["auto_read_message"] is True
