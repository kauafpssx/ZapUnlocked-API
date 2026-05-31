"""Tests for the webhook delivery service."""

from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from src.services.webhooks.service import trigger_webhook


class TestTriggerWebhook:
    CONFIG = {
        "url": "https://example.com/hook",
        "method": "POST",
        "headers": {"Authorization": "Bearer token"},
        "body": {"text": "Hello {{from}}"},
    }

    @patch("src.services.webhooks.service.httpx.AsyncClient")
    async def test_sends_request(self, mock_client_cls):
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.send.return_value = MagicMock(status_code=200)

        await trigger_webhook(self.CONFIG, {"from": "5511999999999"})
        mock_client.send.assert_awaited_once()

    @patch("src.services.webhooks.service.httpx.AsyncClient")
    async def test_uses_default_payload_when_no_body(self, mock_client_cls):
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        await trigger_webhook(
            {"url": "https://example.com", "method": "POST"},
            {"from": "5511999999999"},
            default_payload={"event": "test"},
        )
        args = mock_client.build_request.call_args
        assert args is not None

    @patch("src.services.webhooks.service.httpx.AsyncClient")
    async def test_replaces_placeholders(self, mock_client_cls):
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        config = {
            "url": "https://example.com",
            "method": "POST",
            "body": {"phone": "{{phone}}"},
        }
        await trigger_webhook(config, {"phone": "5511999999999"})
        mock_client.send.assert_awaited_once()

    @patch("src.services.webhooks.service.httpx.AsyncClient")
    async def test_skips_when_no_url(self, mock_client_cls):
        await trigger_webhook({"url": None}, {})
        mock_client_cls.assert_not_called()
