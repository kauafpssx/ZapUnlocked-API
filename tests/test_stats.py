"""Tests for src/services/stats.py — persistent counters in SQLite."""

import pytest

import src.services.stats as stats_module
from src.services.stats import (
    get_all,
    get_webhook_stats,
    increment,
    increment_webhook,
    reset,
    reset_webhook_stats,
)


class TestIncrement:
    def test_increments_known_key(self, temp_db):
        increment("messages_sent", session_id="1")
        result = get_all(session_id="1")
        assert result["messages_sent"] == 1

    def test_increments_multiple_times(self, temp_db):
        increment("messages_sent", session_id="1")
        increment("messages_sent", session_id="1")
        increment("messages_sent", 3, session_id="1")
        result = get_all(session_id="1")
        assert result["messages_sent"] == 5

    def test_ignores_unknown_key(self, temp_db):
        increment("nonexistent_key", session_id="1")
        result = get_all(session_id="1")
        assert "nonexistent_key" not in result

    def test_increments_per_session(self, temp_db):
        increment("messages_sent", session_id="1")
        increment("messages_sent", session_id="1")
        increment("messages_sent", session_id="2")
        assert get_all(session_id="1")["messages_sent"] == 2
        assert get_all(session_id="2")["messages_sent"] == 1

    def test_increments_webhooks_fired(self, temp_db):
        increment("webhooks_fired", 5, session_id="1")
        result = get_all(session_id="1")
        assert result["webhooks_fired"] == 5


class TestGetAll:
    def test_returns_all_counter_keys(self, temp_db):
        result = get_all(session_id="1")
        assert set(result.keys()) == {"messages_sent", "messages_received", "webhooks_fired"}

    def test_defaults_all_to_zero(self, temp_db):
        result = get_all(session_id="1")
        assert all(v == 0 for v in result.values())


class TestIncrementWebhook:
    def test_creates_webhook_stats_entry(self, temp_db):
        increment_webhook("my-hook", session_id="1")
        result = get_webhook_stats("my-hook", session_id="1")
        assert result is not None
        assert result["fired"] == 1
        assert result["last_fired"] is not None

    def test_increments_existing_entry(self, temp_db):
        increment_webhook("my-hook", session_id="1")
        increment_webhook("my-hook", session_id="1")
        result = get_webhook_stats("my-hook", session_id="1")
        assert result["fired"] == 2

    def test_separate_per_session(self, temp_db):
        increment_webhook("hook", session_id="1")
        increment_webhook("hook", session_id="2")
        increment_webhook("hook", session_id="2")
        assert get_webhook_stats("hook", session_id="1")["fired"] == 1
        assert get_webhook_stats("hook", session_id="2")["fired"] == 2


class TestGetWebhookStats:
    def test_returns_none_for_unknown_webhook(self, temp_db):
        result = get_webhook_stats("ghost", session_id="1")
        assert result is None

    def test_returns_all_webhooks_when_name_is_none(self, temp_db):
        increment_webhook("alpha", session_id="1")
        increment_webhook("beta", session_id="1")
        result = get_webhook_stats(session_id="1")
        assert "alpha" in result
        assert "beta" in result

    def test_returns_empty_dict_when_no_webhooks(self, temp_db):
        result = get_webhook_stats(session_id="1")
        assert result == {}


class TestReset:
    def test_clears_all_counters(self, temp_db):
        increment("messages_sent", 5, session_id="1")
        increment_webhook("hook", session_id="1")
        reset(session_id="1")
        result = get_all(session_id="1")
        assert all(v == 0 for v in result.values())
        assert get_webhook_stats(session_id="1") == {}

    def test_reset_only_affects_target_session(self, temp_db):
        increment("messages_sent", 3, session_id="1")
        increment("messages_sent", 2, session_id="2")
        reset(session_id="1")
        assert get_all(session_id="1")["messages_sent"] == 0
        assert get_all(session_id="2")["messages_sent"] == 2


class TestResetWebhookStats:
    def test_resets_specific_webhook(self, temp_db):
        increment_webhook("hook-a", session_id="1")
        increment_webhook("hook-b", session_id="1")
        reset_webhook_stats("hook-a", session_id="1")
        result = get_webhook_stats("hook-a", session_id="1")
        assert result["fired"] == 0
        assert get_webhook_stats("hook-b", session_id="1")["fired"] == 1

    def test_resets_all_when_name_none(self, temp_db):
        increment_webhook("hook-a", session_id="1")
        increment_webhook("hook-b", session_id="1")
        reset_webhook_stats(session_id="1")
        assert get_webhook_stats(session_id="1") == {}
