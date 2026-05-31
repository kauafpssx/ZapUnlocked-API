import json
from unittest.mock import patch

import pytest


@pytest.fixture
def storage():
    with patch("src.services.whatsapp.storage.CHATS_DIR") as mock_dir:
        with patch("src.services.whatsapp.storage.INDEX_FILE") as mock_index:
            mock_dir.__str__ = lambda s: str(s)
            mock_index.__str__ = lambda s: str(s)
            yield


class TestSaveChatIndex:
    async def test_creates_index_when_nonexistent(self, tmp_path):
        index_file = tmp_path / "chats" / "index.json"
        index_file.parent.mkdir(parents=True)
        with patch("src.services.whatsapp.storage.INDEX_FILE", index_file):
            from src.services.whatsapp.storage import save_chat_index
            chat_info = {"id": "5511999999999@s.whatsapp.net", "phone": "5511999999999", "name": "John"}
            await save_chat_index(chat_info)
            data = json.loads(index_file.read_text())
            assert "5511999999999@s.whatsapp.net" in data
            assert data["5511999999999@s.whatsapp.net"]["name"] == "John"

    async def test_updates_existing_index(self, tmp_path):
        index_file = tmp_path / "chats" / "index.json"
        index_file.parent.mkdir(parents=True)
        index_file.write_text(json.dumps({"5511999999999@s.whatsapp.net": {"name": "John"}}))
        with patch("src.services.whatsapp.storage.INDEX_FILE", index_file):
            from src.services.whatsapp.storage import save_chat_index
            await save_chat_index({"id": "5511999999999@s.whatsapp.net", "name": "John Updated"})
            data = json.loads(index_file.read_text())
            assert data["5511999999999@s.whatsapp.net"]["name"] == "John Updated"

    async def test_extracts_phone_from_jid(self, tmp_path):
        index_file = tmp_path / "chats" / "index.json"
        index_file.parent.mkdir(parents=True)
        with patch("src.services.whatsapp.storage.INDEX_FILE", index_file):
            from src.services.whatsapp.storage import save_chat_index
            await save_chat_index({"id": "5511999999999@s.whatsapp.net"})
            data = json.loads(index_file.read_text())
            entry = data["5511999999999@s.whatsapp.net"]
            assert "id" in entry
            assert entry["id"] == "5511999999999@s.whatsapp.net"

    async def test_handles_exception_gracefully(self):
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = Exception("permission denied")
            from src.services.whatsapp.storage import save_chat_index
            await save_chat_index({"id": "test"})  # should not raise


class TestGetRecentChatsFromIndex:
    def test_returns_empty_when_no_index(self, tmp_path):
        index_file = tmp_path / "chats" / "index.json"
        with patch("src.services.whatsapp.storage.INDEX_FILE", index_file):
            from src.services.whatsapp.storage import get_recent_chats_from_index
            result = get_recent_chats_from_index()
            assert result == []

    def test_returns_empty_when_index_empty(self, tmp_path):
        index_file = tmp_path / "chats" / "index.json"
        index_file.parent.mkdir(parents=True)
        index_file.write_text("")
        with patch("src.services.whatsapp.storage.INDEX_FILE", index_file):
            from src.services.whatsapp.storage import get_recent_chats_from_index
            result = get_recent_chats_from_index()
            assert result == []

    def test_returns_sorted_by_timestamp(self, tmp_path):
        index_file = tmp_path / "chats" / "index.json"
        index_file.parent.mkdir(parents=True)
        index_file.write_text(json.dumps({
            "a": {"name": "Old", "lastMessageTimestamp": 1},
            "b": {"name": "New", "lastMessageTimestamp": 3},
            "c": {"name": "Mid", "lastMessageTimestamp": 2},
        }))
        with patch("src.services.whatsapp.storage.INDEX_FILE", index_file):
            from src.services.whatsapp.storage import get_recent_chats_from_index
            result = get_recent_chats_from_index()
            assert [c["name"] for c in result] == ["New", "Mid", "Old"]

    def test_handles_missing_timestamp(self, tmp_path):
        index_file = tmp_path / "chats" / "index.json"
        index_file.parent.mkdir(parents=True)
        index_file.write_text(json.dumps({"a": {"name": "NoTS"}, "b": {"name": "HasTS", "lastMessageTimestamp": 5}}))
        with patch("src.services.whatsapp.storage.INDEX_FILE", index_file):
            from src.services.whatsapp.storage import get_recent_chats_from_index
            result = get_recent_chats_from_index()
            assert result[0]["name"] == "HasTS"

    def test_handles_exception_returns_empty(self, tmp_path):
        index_file = tmp_path / "chats" / "index.json"
        with patch("src.services.whatsapp.storage.INDEX_FILE", index_file):
            with patch("json.loads", side_effect=Exception("bad json")):
                from src.services.whatsapp.storage import get_recent_chats_from_index
                result = get_recent_chats_from_index()
                assert result == []


class TestAddMessageToHistory:
    async def test_creates_new_history_file(self, tmp_path):
        chats_dir = tmp_path / "chats"
        chats_dir.mkdir()
        with patch("src.services.whatsapp.storage.CHATS_DIR", chats_dir):
            from src.services.whatsapp.storage import add_message_to_history
            await add_message_to_history("5511999999999", {"key": {"id": "msg_1"}, "message": {"conversation": "Hi"}})
            file_path = chats_dir / "5511999999999.json.gz"
            assert file_path.exists()

    async def test_appends_to_existing_history(self, tmp_path):
        chats_dir = tmp_path / "chats"
        chats_dir.mkdir()
        with patch("src.services.whatsapp.storage.CHATS_DIR", chats_dir):
            from src.services.whatsapp.storage import add_message_to_history
            await add_message_to_history("5511999999999", {"key": {"id": "msg_1"}})
            await add_message_to_history("5511999999999", {"key": {"id": "msg_2"}})
            file_path = chats_dir / "5511999999999.json.gz"
            import gzip
            data = json.loads(gzip.open(file_path, "rt").read())
            assert len(data) == 2

    async def test_deduplicates_by_id(self, tmp_path):
        chats_dir = tmp_path / "chats"
        chats_dir.mkdir()
        with patch("src.services.whatsapp.storage.CHATS_DIR", chats_dir):
            from src.services.whatsapp.storage import add_message_to_history
            await add_message_to_history("5511999999999", {"key": {"id": "msg_1"}})
            await add_message_to_history("5511999999999", {"key": {"id": "msg_1"}})
            import gzip
            file_path = chats_dir / "5511999999999.json.gz"
            data = json.loads(gzip.open(file_path, "rt").read())
            assert len(data) == 1

    async def test_enforces_history_limit(self, tmp_path):
        chats_dir = tmp_path / "chats"
        chats_dir.mkdir()
        with patch("src.services.whatsapp.storage.CHATS_DIR", chats_dir):
            with patch("src.services.whatsapp.storage.HISTORY_LIMIT", 3):
                from src.services.whatsapp.storage import add_message_to_history
                for i in range(10):
                    await add_message_to_history("5511999999999", {"key": {"id": f"msg_{i}"}})
                import gzip
                file_path = chats_dir / "5511999999999.json.gz"
                data = json.loads(gzip.open(file_path, "rt").read())
                assert len(data) == 3

    async def test_sanitizes_phone(self, tmp_path):
        chats_dir = tmp_path / "chats"
        chats_dir.mkdir()
        with patch("src.services.whatsapp.storage.CHATS_DIR", chats_dir):
            from src.services.whatsapp.storage import add_message_to_history
            await add_message_to_history("55119 9999-9999", {"key": {"id": "msg_1"}})
            file_path = chats_dir / "55119 9999-9999.json.gz"
            assert not file_path.exists()

    async def test_handles_empty_phone(self, tmp_path):
        chats_dir = tmp_path / "chats"
        chats_dir.mkdir()
        with patch("src.services.whatsapp.storage.CHATS_DIR", chats_dir):
            from src.services.whatsapp.storage import add_message_to_history
            await add_message_to_history("", {"key": {"id": "msg_1"}})
            assert len(list(chats_dir.iterdir())) == 0

    async def test_handles_exception_gracefully(self):
        with patch("gzip.open", side_effect=Exception("io error")):
            from src.services.whatsapp.storage import add_message_to_history
            await add_message_to_history("5511999999999", {"key": {"id": "msg_1"}})  # should not raise


class TestGetHistory:
    async def test_returns_empty_for_no_phone(self):
        from src.services.whatsapp.storage import get_history
        result = await get_history("")
        assert result == []

    async def test_returns_empty_for_missing_file(self, tmp_path):
        chats_dir = tmp_path / "chats"
        chats_dir.mkdir()
        with patch("src.services.whatsapp.storage.CHATS_DIR", chats_dir):
            from src.services.whatsapp.storage import get_history
            result = await get_history("5511999999999")
            assert result == []

    async def test_reads_existing_history(self, tmp_path):
        chats_dir = tmp_path / "chats"
        chats_dir.mkdir()
        import gzip
        expected = [{"key": {"id": "msg_1"}}]
        with gzip.open(chats_dir / "5511999999999.json.gz", "wt", encoding="utf-8") as f:
            json.dump(expected, f)
        with patch("src.services.whatsapp.storage.CHATS_DIR", chats_dir):
            from src.services.whatsapp.storage import get_history
            result = await get_history("5511999999999")
            assert result == expected

    async def test_handles_exception_returns_empty(self, tmp_path):
        chats_dir = tmp_path / "chats"
        chats_dir.mkdir()
        with patch("src.services.whatsapp.storage.CHATS_DIR", chats_dir):
            from src.services.whatsapp.storage import get_history
            with patch("gzip.open", side_effect=Exception("read error")):
                result = await get_history("5511999999999")
                assert result == []


class TestClearAllData:
    async def test_clears_all_files(self, tmp_path):
        chats_dir = tmp_path / "chats"
        chats_dir.mkdir()
        (chats_dir / "a.json.gz").write_text("a")
        (chats_dir / "b.json.gz").write_text("b")
        with patch("src.services.whatsapp.storage.CHATS_DIR", chats_dir):
            from src.services.whatsapp.storage import clear_all_data
            await clear_all_data()
            assert len(list(chats_dir.iterdir())) == 0

    async def test_handles_nonexistent_dir(self):
        from src.services.whatsapp.storage import clear_all_data
        await clear_all_data()  # should not raise



