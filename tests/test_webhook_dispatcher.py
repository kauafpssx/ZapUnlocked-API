"""Tests for the webhook dispatcher."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.webhooks.dispatcher import dispatch_event, _utc_now


class TestUtcNow:
    def test_returns_iso_format(self):
        result = _utc_now()
        assert result.endswith("Z")
        assert "T" in result


class TestDispatchEvent:
    @pytest.fixture(autouse=True)
    def use_temp_db(self, temp_db):
        pass

    @pytest.fixture(autouse=True)
    def mock_dependencies(self):
        """Mock imports inside dispatch_event body."""
        mock_registry = MagicMock()
        mock_registry.get_active_webhooks_for_event = MagicMock()
        mock_service = MagicMock()
        mock_service.trigger_webhook = AsyncMock()

        with patch.dict("sys.modules", {
            "src.services.webhooks.registry": mock_registry,
            "src.services.webhooks.service": mock_service,
        }):
            yield {
                "get_active_webhooks_for_event": mock_registry.get_active_webhooks_for_event,
                "trigger_webhook": mock_service.trigger_webhook,
            }

    async def test_dispatches_to_active_webhooks(self, mock_dependencies):
        mock_dependencies["get_active_webhooks_for_event"].return_value = [
            {"url": "https://a.com"},
            {"url": "https://b.com"},
        ]
        await dispatch_event("message.text", {"phone": "5511999999999"})
        await asyncio.sleep(0)
        assert mock_dependencies["trigger_webhook"].call_count == 2

    async def test_skips_when_no_webhooks(self, mock_dependencies):
        mock_dependencies["get_active_webhooks_for_event"].return_value = []
        await dispatch_event("message.text", {})
        await asyncio.sleep(0)
        mock_dependencies["trigger_webhook"].assert_not_called()

    async def test_passes_default_payload(self, mock_dependencies):
        mock_dependencies["get_active_webhooks_for_event"].return_value = [
            {"url": "https://example.com"},
        ]
        await dispatch_event("connection.connected", {"phone": "5511999999999"})
        await asyncio.sleep(0)
        args, kwargs = mock_dependencies["trigger_webhook"].call_args
        assert args[0] == {"url": "https://example.com"}
        assert kwargs["default_payload"]["event"] == "connection.connected"
