"""Tests for native-flow sender (Fase 2)."""

import asyncio
import json
from unittest.mock import MagicMock, patch

import pytest

from src.services.whatsapp.sender import native_flow as nf


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture
def mock_client():
    client = MagicMock()
    resp = MagicMock()
    resp.ID = "MSG-NF-1"
    client.send_message.return_value = resp
    return client


def test_send_native_flow_serializes_params_once(mock_client):
    with patch("src.services.whatsapp.sender.native_flow._ensure_client", return_value=mock_client), \
         patch("src.services.whatsapp.sender.native_flow.apply_pre_send", new_callable=__import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock), \
         patch("src.services.whatsapp.sender.native_flow._save_to_history", new_callable=__import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock), \
         patch("src.services.whatsapp.sender.native_flow._dispatch_sent_event", new_callable=__import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock):
        params = {"id": "ok", "display_text": "OK", "nested": {"x": 1}}
        res = asyncio.run(nf.send_native_flow_message(
            "5511999999999",
            "body",
            buttons=[{"name": "quick_reply", "params": params}],
            message_params={"foo": "bar"},
            session_id="1",
        ))
    assert res.ID == "MSG-NF-1"
    mock_client.send_message.assert_called_once()


def test_send_native_flow_accepts_json_strings(mock_client):
    with patch("src.services.whatsapp.sender.native_flow._ensure_client", return_value=mock_client), \
         patch("src.services.whatsapp.sender.native_flow.apply_pre_send", new_callable=__import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock), \
         patch("src.services.whatsapp.sender.native_flow._save_to_history", new_callable=__import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock), \
         patch("src.services.whatsapp.sender.native_flow._dispatch_sent_event", new_callable=__import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock):
        asyncio.run(nf.send_native_flow_message(
            "5511999999999",
            "body",
            buttons=[{"name": "quick_reply", "params": json.dumps({"id": "x"})}],
            message_params=json.dumps({"y": 2}),
            session_id="1",
        ))
    mock_client.send_message.assert_called_once()