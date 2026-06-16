"""Tests for the webhook registry (SQLite-backed CRUD)."""

import pytest

from src.services.webhooks.registry import (
    list_webhooks,
    get_webhook,
    create_webhook,
    update_webhook,
    delete_webhook,
    toggle_webhook,
    get_active_webhooks_for_event,
    _slugify,
)


@pytest.fixture(autouse=True)
def use_temp_db(temp_db):
    pass


class TestSlugify:
    def test_replaces_special_chars(self):
        assert _slugify("My Webhook!") == "My-Webhook"

    def test_truncates_to_64_chars(self):
        long_name = "a" * 100
        assert len(_slugify(long_name)) == 64

    def test_strips_trailing_dashes(self):
        assert _slugify("hello-") == "hello"


class TestCreateWebhook:
    MINIMAL = {"name": "test-hook", "url": "https://example.com/hook"}

    def test_creates_with_defaults(self):
        wh = create_webhook(self.MINIMAL)
        assert wh["name"] == "test-hook"
        assert wh["url"] == "https://example.com/hook"
        assert wh["method"] == "POST"
        assert wh["active"] is True
        assert wh["events"] == ["*"]
        assert "created_at" in wh

    def test_raises_without_name(self):
        with pytest.raises(ValueError, match="name"):
            create_webhook({"url": "https://example.com"})

    def test_raises_on_duplicate(self):
        create_webhook(self.MINIMAL)
        with pytest.raises(ValueError, match="already exists"):
            create_webhook(self.MINIMAL)

    def test_creates_with_custom_events(self):
        wh = create_webhook({**self.MINIMAL, "events": ["message.text"]})
        assert wh["events"] == ["message.text"]


class TestGetWebhook:
    def test_returns_none_for_missing(self):
        assert get_webhook("nonexistent") is None

    def test_returns_existing(self):
        create_webhook({"name": "my-hook", "url": "https://example.com"})
        wh = get_webhook("my-hook")
        assert wh is not None
        assert wh["name"] == "my-hook"


class TestListWebhooks:
    def test_returns_empty_list(self):
        assert list_webhooks() == []

    def test_returns_all_webhooks(self):
        create_webhook({"name": "a", "url": "https://a.com"})
        create_webhook({"name": "b", "url": "https://b.com"})
        hooks = list_webhooks()
        assert len(hooks) == 2


class TestUpdateWebhook:
    def test_updates_fields(self):
        create_webhook({"name": "test", "url": "https://old.com"})
        updated = update_webhook("test", {"url": "https://new.com", "active": False})
        assert updated["url"] == "https://new.com"
        assert updated["active"] is False

    def test_raises_for_missing(self):
        with pytest.raises(ValueError, match="not found"):
            update_webhook("nope", {"url": "https://x.com"})


class TestDeleteWebhook:
    def test_deletes_existing(self):
        create_webhook({"name": "test", "url": "https://example.com"})
        delete_webhook("test")
        assert get_webhook("test") is None

    def test_raises_for_missing(self):
        with pytest.raises(ValueError, match="not found"):
            delete_webhook("nope")


class TestToggleWebhook:
    def test_toggles_active_state(self):
        create_webhook({"name": "test", "url": "https://example.com"})
        wh = toggle_webhook("test", False)
        assert wh["active"] is False
        wh = toggle_webhook("test", True)
        assert wh["active"] is True

    def test_raises_for_missing(self):
        with pytest.raises(ValueError, match="not found"):
            toggle_webhook("nope", True)


class TestGetActiveWebhooksForEvent:
    def test_wildcard_matches_all(self):
        create_webhook({"name": "all", "url": "https://example.com", "events": ["*"]})
        result = get_active_webhooks_for_event("message.text")
        assert len(result) == 1

    def test_inactive_webhook_excluded(self):
        create_webhook({"name": "off", "url": "https://example.com", "active": False})
        result = get_active_webhooks_for_event("message.text")
        assert result == []

    def test_event_filtering(self):
        create_webhook({"name": "text-only", "url": "https://example.com", "events": ["message.text"]})
        assert len(get_active_webhooks_for_event("message.text")) == 1
        assert len(get_active_webhooks_for_event("message.image")) == 0

    def test_multiple_webhooks_returned(self):
        create_webhook({"name": "a", "url": "https://a.com", "events": ["message.text"]})
        create_webhook({"name": "b", "url": "https://b.com", "events": ["message.text"]})
        result = get_active_webhooks_for_event("message.text")
        assert len(result) == 2
