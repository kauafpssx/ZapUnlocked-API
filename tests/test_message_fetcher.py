from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_client():
    cli = MagicMock()
    cli.__bool__ = lambda s: True
    return cli


@pytest.fixture
def history():
    return [
        {"key": {"remoteJid": "111@s.whatsapp.net", "id": "m1", "fromMe": False}, "message": {"conversation": "Hello"}, "messageTimestamp": 100},
        {"key": {"remoteJid": "111@s.whatsapp.net", "id": "m2", "fromMe": True}, "message": {"extendedTextMessage": {"text": "Hi back"}}, "messageTimestamp": 200},
    ]


class TestFetchMessages:
    async def test_raises_when_not_connected(self):
        with patch("src.services.whatsapp.messageFetcher.get_client", return_value=None):
            from src.services.whatsapp.messageFetcher import fetch_messages
            with pytest.raises(Exception, match="WhatsApp is not connected"):
                await fetch_messages("111@s.whatsapp.net")

    async def test_returns_empty_when_no_history(self, mock_client):
        with patch("src.services.whatsapp.messageFetcher.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.storage.get_history", new_callable=AsyncMock, return_value=[]):
                from src.services.whatsapp.messageFetcher import fetch_messages
                result = await fetch_messages("111@s.whatsapp.net")
                assert result["found"] == 0
                assert result["messages"] == []

    async def test_processes_conversation_messages(self, mock_client, history):
        with patch("src.services.whatsapp.messageFetcher.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.storage.get_history", new_callable=AsyncMock, return_value=history):
                from src.services.whatsapp.messageFetcher import fetch_messages
                result = await fetch_messages("111@s.whatsapp.net")
                texts = [m["text"] for m in result["messages"]]
                assert "Hello" in texts
                assert "Hi back" in texts

    async def test_filters_by_msg_type_sent(self, mock_client, history):
        with patch("src.services.whatsapp.messageFetcher.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.storage.get_history", new_callable=AsyncMock, return_value=history):
                from src.services.whatsapp.messageFetcher import fetch_messages
                result = await fetch_messages("111@s.whatsapp.net", msg_type="sent")
                assert all(m["fromMe"] for m in result["messages"])

    async def test_filters_by_msg_type_received(self, mock_client, history):
        with patch("src.services.whatsapp.messageFetcher.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.storage.get_history", new_callable=AsyncMock, return_value=history):
                from src.services.whatsapp.messageFetcher import fetch_messages
                result = await fetch_messages("111@s.whatsapp.net", msg_type="received")
                assert all(not m["fromMe"] for m in result["messages"])

    async def test_filters_by_query(self, mock_client, history):
        with patch("src.services.whatsapp.messageFetcher.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.storage.get_history", new_callable=AsyncMock, return_value=history):
                from src.services.whatsapp.messageFetcher import fetch_messages
                result = await fetch_messages("111@s.whatsapp.net", options={"query": "Hello"})
                texts = [m["text"] for m in result["messages"]]
                assert "Hello" in texts
                assert "Hi back" not in texts

    async def test_filters_by_only_buttons(self, mock_client):
        history_with_button = [
            {"key": {"remoteJid": "111@s.whatsapp.net", "id": "m1", "fromMe": False}, "message": {"buttonsMessage": {"contentText": "Click"}}, "messageTimestamp": 100},
            {"key": {"remoteJid": "111@s.whatsapp.net", "id": "m2", "fromMe": False}, "message": {"conversation": "plain"}, "messageTimestamp": 200},
        ]
        with patch("src.services.whatsapp.messageFetcher.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.storage.get_history", new_callable=AsyncMock, return_value=history_with_button):
                from src.services.whatsapp.messageFetcher import fetch_messages
                result = await fetch_messages("111@s.whatsapp.net", options={"onlyButtons": True})
                assert len(result["messages"]) == 1

    async def test_extracts_reactions_from_global_cache(self, mock_client):
        history = [
            {"key": {"remoteJid": "111@s.whatsapp.net", "id": "m1", "fromMe": False}, "message": {"conversation": "Hi"}, "messageTimestamp": 100},
        ]
        with patch("src.services.whatsapp.messageFetcher.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.storage.get_history", new_callable=AsyncMock, return_value=history):
                with patch("src.services.whatsapp.messageFetcher.get_reaction_cache", return_value={"m1": "👍"}):
                    from src.services.whatsapp.messageFetcher import fetch_messages
                    result = await fetch_messages("111@s.whatsapp.net")
                    assert result["messages"][0]["reaction"] == "👍"

    async def test_handles_stub_messages(self, mock_client):
        history = [
            {"key": {"remoteJid": "111@s.whatsapp.net", "id": "m1", "fromMe": False}, "messageStubType": 1, "message": {"conversation": "test"}, "messageTimestamp": 100},
        ]
        with patch("src.services.whatsapp.messageFetcher.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.storage.get_history", new_callable=AsyncMock, return_value=history):
                from src.services.whatsapp.messageFetcher import fetch_messages
                result = await fetch_messages("111@s.whatsapp.net")
                assert "[revoke]" in result["messages"][0]["text"]

    async def test_handles_reaction_messages(self, mock_client):
        history = [
            {"key": {"remoteJid": "111@s.whatsapp.net", "id": "m1", "fromMe": False},
             "message": {"reactionMessage": {"key": {"id": "target"}, "text": "❤️"}},
             "messageTimestamp": 100},
        ]
        with patch("src.services.whatsapp.messageFetcher.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.storage.get_history", new_callable=AsyncMock, return_value=history):
                from src.services.whatsapp.messageFetcher import fetch_messages
                result = await fetch_messages("111@s.whatsapp.net")
                assert "[reaction:" in result["messages"][0]["text"]

    async def test_handles_image_message(self, mock_client):
        history = [
            {"key": {"remoteJid": "111@s.whatsapp.net", "id": "m1", "fromMe": False},
             "message": {"imageMessage": {"caption": "Nice pic", "mimetype": "image/jpeg"}},
             "messageTimestamp": 100},
        ]
        with patch("src.services.whatsapp.messageFetcher.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.storage.get_history", new_callable=AsyncMock, return_value=history):
                from src.services.whatsapp.messageFetcher import fetch_messages
                result = await fetch_messages("111@s.whatsapp.net")
                assert result["messages"][0]["text"] == "Nice pic"

    async def test_limits_result_count(self, mock_client):
        history = [
            {"key": {"remoteJid": "111@s.whatsapp.net", "id": f"m{i}", "fromMe": False},
             "message": {"conversation": f"msg {i}"}, "messageTimestamp": i}
            for i in range(10)
        ]
        with patch("src.services.whatsapp.messageFetcher.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.storage.get_history", new_callable=AsyncMock, return_value=history):
                from src.services.whatsapp.messageFetcher import fetch_messages
                result = await fetch_messages("111@s.whatsapp.net", limit=3)
                assert len(result["messages"]) == 3
                assert result["found"] == 3

    async def test_removes_raw_field(self, mock_client, history):
        with patch("src.services.whatsapp.messageFetcher.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.storage.get_history", new_callable=AsyncMock, return_value=history):
                from src.services.whatsapp.messageFetcher import fetch_messages
                result = await fetch_messages("111@s.whatsapp.net")
                assert "_raw" not in result["messages"][0]

    async def test_handles_image_without_caption(self, mock_client):
        history = [
            {"key": {"remoteJid": "111@s.whatsapp.net", "id": "m1", "fromMe": False},
             "message": {"imageMessage": {"mimetype": "image/png"}},
             "messageTimestamp": 100},
        ]
        with patch("src.services.whatsapp.messageFetcher.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.storage.get_history", new_callable=AsyncMock, return_value=history):
                from src.services.whatsapp.messageFetcher import fetch_messages
                result = await fetch_messages("111@s.whatsapp.net")
                assert result["messages"][0]["text"] == "[image_message]"

    async def test_skips_non_dict_messages(self, mock_client):
        history = [{"key": {"remoteJid": "111@s.whatsapp.net", "id": "m1"}, "messageTimestamp": 100, "message": {"conversation": "valid"}}, "not_a_dict"]
        with patch("src.services.whatsapp.messageFetcher.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.storage.get_history", new_callable=AsyncMock, return_value=history):
                from src.services.whatsapp.messageFetcher import fetch_messages
                result = await fetch_messages("111@s.whatsapp.net")
                assert len(result["messages"]) == 1


class TestGetRecentChats:
    def test_returns_limited_chats(self):
        with patch("src.services.whatsapp.messageFetcher.storage.get_recent_chats_from_index", return_value=[{"id": "c1"}, {"id": "c2"}, {"id": "c3"}]):
            from src.services.whatsapp.messageFetcher import get_recent_chats
            result = get_recent_chats(limit=2)
            assert len(result) == 2

    def test_returns_all_when_limit_exceeds(self):
        with patch("src.services.whatsapp.messageFetcher.storage.get_recent_chats_from_index", return_value=[{"id": "c1"}]):
            from src.services.whatsapp.messageFetcher import get_recent_chats
            result = get_recent_chats(limit=10)
            assert len(result) == 1

    def test_returns_empty_when_no_chats(self):
        with patch("src.services.whatsapp.messageFetcher.storage.get_recent_chats_from_index", return_value=[]):
            from src.services.whatsapp.messageFetcher import get_recent_chats
            assert get_recent_chats() == []
