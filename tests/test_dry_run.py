"""Tests for src/utils/dry_run.py."""

import pytest

from src.utils.dry_run import dry_run_media_response, dry_run_response, is_dry_run


class TestIsDryRun:
    def test_false_by_default(self, monkeypatch):
        monkeypatch.delenv("DRY_RUN", raising=False)
        assert is_dry_run() is False

    def test_true_when_set_to_true(self, monkeypatch):
        monkeypatch.setenv("DRY_RUN", "true")
        assert is_dry_run() is True

    def test_true_when_set_to_1(self, monkeypatch):
        monkeypatch.setenv("DRY_RUN", "1")
        assert is_dry_run() is True

    def test_true_when_set_to_yes(self, monkeypatch):
        monkeypatch.setenv("DRY_RUN", "yes")
        assert is_dry_run() is True

    def test_true_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("DRY_RUN", "TRUE")
        assert is_dry_run() is True

    def test_false_when_set_to_false(self, monkeypatch):
        monkeypatch.setenv("DRY_RUN", "false")
        assert is_dry_run() is False

    def test_false_when_set_to_0(self, monkeypatch):
        monkeypatch.setenv("DRY_RUN", "0")
        assert is_dry_run() is False


class TestDryRunResponse:
    def test_default_message(self):
        res = dry_run_response()
        assert res["success"] is True
        assert res["dryRun"] is True
        assert res["message"] == "Message sent."
        assert res["messageId"] is None
        assert "timestamp" in res

    def test_custom_message(self):
        res = dry_run_response("Custom msg")
        assert res["message"] == "Custom msg"

    def test_timestamp_is_iso_format(self):
        import re
        res = dry_run_response()
        assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", res["timestamp"])


class TestDryRunMediaResponse:
    def test_default_message(self):
        res = dry_run_media_response()
        assert res["success"] is True
        assert res["dryRun"] is True
        assert res["message"] == "Media queued."

    def test_custom_message(self):
        res = dry_run_media_response("Uploading...")
        assert res["message"] == "Uploading..."

    def test_no_message_id_or_timestamp(self):
        res = dry_run_media_response()
        assert "messageId" not in res
        assert "timestamp" not in res
