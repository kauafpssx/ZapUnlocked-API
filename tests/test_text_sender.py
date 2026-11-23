import asyncio
from unittest.mock import MagicMock

import pytest

from src.services.whatsapp.sender.text import _send_with_confirmation


def test_send_requires_message_id():
    client = MagicMock()
    client.send_message.return_value = None

    with pytest.raises(RuntimeError, match="missing message ID"):
        asyncio.run(_send_with_confirmation(client, MagicMock(), "hello"))


def test_send_returns_acknowledged_response():
    client = MagicMock()
    response = MagicMock()
    response.ID = "message-123"
    client.send_message.return_value = response

    assert asyncio.run(_send_with_confirmation(client, MagicMock(), "hello")) is response
