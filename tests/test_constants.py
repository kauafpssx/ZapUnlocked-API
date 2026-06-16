"""Tests for src/config/constants.py — path helpers and env resolution."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config.constants import get_auth_dir, get_data_dir


class TestGetAuthDir:
    def test_includes_session_id(self):
        result = get_auth_dir("my-session")
        assert result.endswith("my-session")

    def test_returns_string(self):
        assert isinstance(get_auth_dir("1"), str)

    def test_session_1_is_subfolder(self):
        result = get_auth_dir("1")
        assert Path(result).name == "1"

    def test_session_id_in_path(self):
        sid = "abc-123"
        result = get_auth_dir(sid)
        assert sid in result


class TestGetDataDir:
    def test_includes_session_id(self):
        result = get_data_dir("session-x")
        assert result.endswith("session-x")

    def test_returns_string(self):
        assert isinstance(get_data_dir("1"), str)

    def test_session_id_in_path(self):
        sid = "test-session"
        result = get_data_dir(sid)
        assert sid in result

    def test_different_sessions_produce_different_paths(self):
        assert get_data_dir("1") != get_data_dir("2")


class TestIsAlwaysdata:
    def test_false_when_no_indicators(self, monkeypatch):
        monkeypatch.delenv("ALWAYSDATA_ACCOUNT", raising=False)
        from src.config import constants
        with patch.object(constants, "_is_alwaysdata", return_value=False):
            assert constants._is_alwaysdata() is False

    def test_true_when_env_set(self, monkeypatch):
        monkeypatch.setenv("ALWAYSDATA_ACCOUNT", "myaccount")
        from src.config import constants
        assert constants._is_alwaysdata() is True
