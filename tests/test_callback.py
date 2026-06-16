from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.handlers.callback import handleMessage


@pytest.fixture
def msg():
    m = MagicMock()
    m.Info.ID = "msg_id_123"
    return m


@pytest.fixture
def parsed():
    return {
        "phone": "5511999999999",
        "text": "Hello",
        "buttonResponse": "",
    }


class TestHandleMessage:
    async def test_ignores_when_should_ignore(self, msg):
        with patch("src.handlers.callback.should_ignore_message", return_value=True) as mock_ignore:
            await handleMessage(None, msg)
            mock_ignore.assert_called_once_with(msg)

    async def test_ignores_when_parse_fails(self, msg):
        with patch("src.handlers.callback.should_ignore_message", return_value=False):
            with patch("src.handlers.callback.parse_message", return_value=None) as mock_parse:
                await handleMessage(None, msg)
                mock_parse.assert_called_once_with(msg)

    async def test_dispatches_normal_message(self, msg, parsed):
        with patch("src.handlers.callback.should_ignore_message", return_value=False):
            with patch("src.handlers.callback.parse_message", return_value=parsed):
                with patch("src.handlers.callback.dispatch_message_event") as mock_dispatch:
                    await handleMessage(None, msg)
                    mock_dispatch.assert_called_once_with(msg, "5511999999999", parsed, "1")

    async def test_callback_in_button_response(self, msg, parsed):
        parsed["buttonResponse"] = "cb=valid_token"
        with patch("src.handlers.callback.should_ignore_message", return_value=False):
            with patch("src.handlers.callback.parse_message", return_value=parsed):
                with patch("src.handlers.callback.verify_and_decode_payload") as mock_verify:
                    mock_verify.return_value = {"url": "https://example.com", "method": "POST", "headers": {}, "body": {}, "reaction": None}
                    with patch("src.handlers.callback.trigger_webhook") as mock_webhook:
                        await handleMessage(None, msg)
                        mock_verify.assert_called_once_with("valid_token")
                        mock_webhook.assert_called_once()

    async def test_callback_in_text(self, msg, parsed):
        parsed["text"] = "Click here|cb=token_in_text"
        parsed["buttonResponse"] = "something"
        with patch("src.handlers.callback.should_ignore_message", return_value=False):
            with patch("src.handlers.callback.parse_message", return_value=parsed):
                with patch("src.handlers.callback.verify_and_decode_payload") as mock_verify:
                    mock_verify.return_value = {"url": "https://example.com", "method": "POST", "headers": {}, "body": {}, "reaction": None}
                    with patch("src.handlers.callback.trigger_webhook") as mock_webhook:
                        await handleMessage(None, msg)
                        mock_verify.assert_called_once_with("token_in_text")
                        mock_webhook.assert_called_once()

    async def test_callback_with_reaction(self, msg, parsed):
        parsed["buttonResponse"] = "cb=react_token"
        with patch("src.handlers.callback.should_ignore_message", return_value=False):
            with patch("src.handlers.callback.parse_message", return_value=parsed):
                with patch("src.handlers.callback.verify_and_decode_payload") as mock_verify:
                    mock_verify.return_value = {"url": None, "method": "POST", "headers": {}, "body": {}, "reaction": "❤️"}
                    with patch("src.services.whatsapp.sender.send_reaction", new_callable=AsyncMock) as mock_react:
                        await handleMessage(None, msg)
                        mock_react.assert_awaited_once_with("5511999999999", "msg_id_123", "❤️")

    async def test_callback_with_url_triggers_webhook(self, msg, parsed):
        parsed["buttonResponse"] = "cb=webhook_token"
        webhook_config = {"url": "https://hook.example.com", "method": "POST", "headers": {}, "body": {}, "reaction": None}
        with patch("src.handlers.callback.should_ignore_message", return_value=False):
            with patch("src.handlers.callback.parse_message", return_value=parsed):
                with patch("src.handlers.callback.verify_and_decode_payload", return_value=webhook_config):
                    with patch("src.handlers.callback.trigger_webhook", new_callable=AsyncMock) as mock_webhook:
                        with patch("asyncio.create_task", side_effect=lambda c: c):
                            await handleMessage(None, msg)
                            mock_webhook.assert_called_once()

    async def test_invalid_callback_logs_warning(self, msg, parsed):
        parsed["buttonResponse"] = "cb=bad_token"
        with patch("src.handlers.callback.should_ignore_message", return_value=False):
            with patch("src.handlers.callback.parse_message", return_value=parsed):
                with patch("src.handlers.callback.verify_and_decode_payload", return_value=None):
                    with patch("src.handlers.callback.logger.warning") as mock_warn:
                        await handleMessage(None, msg)
                        mock_warn.assert_called_once()
                        assert "Invalid" in str(mock_warn.call_args[0][0])

    async def test_callback_reaction_failure_logged(self, msg, parsed):
        parsed["buttonResponse"] = "cb=react_token"
        with patch("src.handlers.callback.should_ignore_message", return_value=False):
            with patch("src.handlers.callback.parse_message", return_value=parsed):
                with patch("src.handlers.callback.verify_and_decode_payload") as mock_verify:
                    mock_verify.return_value = {"url": None, "method": "POST", "headers": {}, "body": {}, "reaction": "👍"}
                    with patch("src.services.whatsapp.sender.send_reaction", new_callable=AsyncMock, side_effect=Exception("reaction failed")):
                        with patch("src.handlers.callback.logger.error") as mock_err:
                            await handleMessage(None, msg)
                            mock_err.assert_called_once()
                            assert "reaction failed" in str(mock_err.call_args[0][0])

    async def test_non_cb_button_response_passes_through(self, msg, parsed):
        parsed["buttonResponse"] = "not_a_callback"
        with patch("src.handlers.callback.should_ignore_message", return_value=False):
            with patch("src.handlers.callback.parse_message", return_value=parsed):
                with patch("src.handlers.callback.dispatch_message_event") as mock_dispatch:
                    await handleMessage(None, msg)
                    mock_dispatch.assert_called_once()
