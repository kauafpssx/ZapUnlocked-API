"""Tests for the HMAC callback token utilities."""

import time
from unittest.mock import patch

import pytest

from src.utils.security.callback_token import (
    create_callback_payload,
    verify_and_decode_payload,
)


class TestCallbackToken:
    """Test the full create/verify cycle."""

    WEBHOOK_CONFIG = {
        "url": "https://example.com/webhook",
        "method": "POST",
        "headers": {"Authorization": "Bearer test"},
        "body": {"key": "value"},
        "reaction": "👍",
    }

    @patch("src.utils.security.callback_token.INTERNAL_SECRET", "test-secret-key")
    def test_create_and_verify_cycle(self):
        """Creating a token and verifying it should return the original config."""
        token = create_callback_payload(self.WEBHOOK_CONFIG)
        assert isinstance(token, str)
        assert len(token) > 10

        result = verify_and_decode_payload(token)
        assert result is not None
        assert result["url"] == self.WEBHOOK_CONFIG["url"]
        assert result["method"] == "POST"
        assert result["reaction"] == "👍"
        assert result["headers"]["Authorization"] == "Bearer test"
        assert result["body"]["key"] == "value"

    @patch("src.utils.security.callback_token.INTERNAL_SECRET", "test-secret-key")
    def test_tampered_token_returns_none(self):
        """A tampered token should fail verification."""
        token = create_callback_payload(self.WEBHOOK_CONFIG)
        tampered = token[:-3] + "abc"
        result = verify_and_decode_payload(tampered)
        assert result is None

    @patch("src.utils.security.callback_token.INTERNAL_SECRET", "test-secret-key")
    def test_invalid_token_returns_none(self):
        """A completely invalid token should return None."""
        result = verify_and_decode_payload("not-a-valid-token")
        assert result is None

    @patch("src.utils.security.callback_token.INTERNAL_SECRET", "test-secret-key")
    def test_empty_string_returns_none(self):
        result = verify_and_decode_payload("")
        assert result is None

    @patch("src.utils.security.callback_token.INTERNAL_SECRET", "test-secret-key")
    def test_minimal_webhook_config(self):
        """A minimal webhook config should work (no reaction, no headers)."""
        config = {
            "url": "https://example.com/hook",
        }
        token = create_callback_payload(config)
        result = verify_and_decode_payload(token)
        assert result is not None
        assert result["url"] == config["url"]
        assert result["reaction"] is None

    @patch("src.utils.security.callback_token.INTERNAL_SECRET", None)
    def test_no_secret_raises_error(self):
        """create_callback_payload should raise if INTERNAL_SECRET is not set."""
        with pytest.raises(RuntimeError, match="INTERNAL_SECRET"):
            create_callback_payload({"url": "https://example.com/hook"})


class TestCallbackTokenExpiry:
    """Test token expiry behavior."""

    WEBHOOK_CONFIG = {"url": "https://example.com/webhook"}

    @patch("src.utils.security.callback_token.INTERNAL_SECRET", "test-secret-key")
    def test_expired_token_returns_none(self):
        """Create a token with a past expiry by mocking time.time."""
        original_time = time.time

        # Mock time to be 48 hours in the future (after token expiry)
        with patch("src.utils.security.callback_token.time.time") as mock_time:
            # First call to time.time during creation: current time
            # We need the token to be created NOW
            mock_time.return_value = original_time()

            token = create_callback_payload(self.WEBHOOK_CONFIG)

        # Now verify with a time >24h in the future
        with patch("src.utils.security.callback_token.time.time") as mock_time:
            mock_time.return_value = original_time() + 48 * 3600  # 48h later
            result = verify_and_decode_payload(token)
            assert result is None
