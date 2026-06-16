"""Tests for src/utils/time.py — now_ts(), sent_response(), _resolve_tz_name()."""

import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import src.utils.time as time_module
from src.utils.time import _resolve_tz_name, now_ts, sent_response


class TestResolveTzName:
    def test_returns_utc_when_no_conf_and_no_env(self, monkeypatch, tmp_path):
        monkeypatch.setattr(time_module, "_CONF", tmp_path / "timezone.conf")
        monkeypatch.delenv("TZ", raising=False)
        with patch.dict("src.utils.time.__dict__", {"_CONF": tmp_path / "timezone.conf"}):
            result = _resolve_tz_name()
        assert result == "UTC"

    def test_reads_tz_from_env(self, monkeypatch, tmp_path):
        monkeypatch.setattr(time_module, "_CONF", tmp_path / "nonexistent.conf")
        monkeypatch.setenv("TZ", "America/Sao_Paulo")
        result = _resolve_tz_name()
        assert result == "America/Sao_Paulo"

    def test_reads_tz_from_conf_file(self, monkeypatch, tmp_path):
        conf = tmp_path / "timezone.conf"
        conf.write_text("# comment\nEurope/Berlin\n", encoding="utf-8")
        monkeypatch.setattr(time_module, "_CONF", conf)
        monkeypatch.delenv("TZ", raising=False)
        result = _resolve_tz_name()
        assert result == "Europe/Berlin"

    def test_conf_file_ignores_comments(self, monkeypatch, tmp_path):
        conf = tmp_path / "timezone.conf"
        conf.write_text("# this is a comment\nAsia/Tokyo\n", encoding="utf-8")
        monkeypatch.setattr(time_module, "_CONF", conf)
        monkeypatch.delenv("TZ", raising=False)
        result = _resolve_tz_name()
        assert result == "Asia/Tokyo"


class TestNowTs:
    def test_returns_iso_format_string(self):
        result = now_ts()
        assert isinstance(result, str)
        assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", result)

    def test_returns_string_each_call(self):
        r1 = now_ts()
        r2 = now_ts()
        assert isinstance(r1, str)
        assert isinstance(r2, str)


class TestSentResponse:
    def test_success_true(self):
        res = sent_response(None)
        assert res["success"] is True

    def test_default_message(self):
        res = sent_response(None)
        assert res["message"] == "Message sent."

    def test_custom_message(self):
        res = sent_response(None, "Audio sent.")
        assert res["message"] == "Audio sent."

    def test_message_id_from_res_id_attr(self):
        mock_res = MagicMock()
        mock_res.ID = "abc123"
        res = sent_response(mock_res)
        assert res["messageId"] == "abc123"

    def test_message_id_none_when_res_none(self):
        res = sent_response(None)
        assert res["messageId"] is None

    def test_message_id_none_when_no_id_attr(self):
        mock_res = MagicMock(spec=[])
        res = sent_response(mock_res)
        assert res["messageId"] is None

    def test_timestamp_is_present(self):
        res = sent_response(None)
        assert "timestamp" in res
        assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", res["timestamp"])
