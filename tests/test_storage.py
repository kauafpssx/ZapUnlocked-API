import json
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def use_temp_db(temp_db):
    pass


class TestSaveChatIndex:
    async def test_creates_index_entry(self):
        from src.services.whatsapp.storage import save_chat_index, get_recent_chats_from_index
        chat_info = {"id": "5511999999999@s.whatsapp.net", "phone": "5511999999999", "name": "John"}
        await save_chat_index(chat_info)
        chats = get_recent_chats_from_index()
        assert any(c["id"] == "5511999999999@s.whatsapp.net" for c in chats)
        assert any(c["name"] == "John" for c in chats)

    async def test_updates_existing_entry(self):
        from src.services.whatsapp.storage import save_chat_index, get_recent_chats_from_index
        await save_chat_index({"id": "5511999999999@s.whatsapp.net", "name": "John"})
        await save_chat_index({"id": "5511999999999@s.whatsapp.net", "name": "John Updated"})
        chats = get_recent_chats_from_index()
        entry = next(c for c in chats if c["id"] == "5511999999999@s.whatsapp.net")
        assert entry["name"] == "John Updated"

    async def test_extracts_phone_from_jid(self):
        from src.services.whatsapp.storage import save_chat_index, get_recent_chats_from_index
        await save_chat_index({"id": "5511999999999@s.whatsapp.net"})
        chats = get_recent_chats_from_index()
        entry = next(c for c in chats if c["id"] == "5511999999999@s.whatsapp.net")
        assert entry["phone"] == "5511999999999"

    async def test_skips_entry_without_id(self):
        from src.services.whatsapp.storage import save_chat_index, get_recent_chats_from_index
        await save_chat_index({"phone": "5511999999999"})  # no id
        assert get_recent_chats_from_index() == []

    async def test_handles_exception_gracefully(self):
        from src.services.whatsapp.storage import save_chat_index
        with patch("src.services.whatsapp.storage.get_conn", side_effect=Exception("db error")):
            await save_chat_index({"id": "test"})  # should not raise


class TestGetRecentChatsFromIndex:
    def test_returns_empty_when_no_entries(self):
        from src.services.whatsapp.storage import get_recent_chats_from_index
        assert get_recent_chats_from_index() == []

    async def test_returns_sorted_by_timestamp(self):
        from src.services.whatsapp.storage import save_chat_index, get_recent_chats_from_index
        await save_chat_index({"id": "a", "name": "Old", "lastMessageTimestamp": 1})
        await save_chat_index({"id": "b", "name": "New", "lastMessageTimestamp": 3})
        await save_chat_index({"id": "c", "name": "Mid", "lastMessageTimestamp": 2})
        result = get_recent_chats_from_index()
        assert [c["name"] for c in result] == ["New", "Mid", "Old"]

    async def test_handles_missing_timestamp(self):
        from src.services.whatsapp.storage import save_chat_index, get_recent_chats_from_index
        await save_chat_index({"id": "a", "name": "NoTS"})
        await save_chat_index({"id": "b", "name": "HasTS", "lastMessageTimestamp": 5})
        result = get_recent_chats_from_index()
        assert result[0]["name"] == "HasTS"

    def test_handles_exception_returns_empty(self):
        from src.services.whatsapp.storage import get_recent_chats_from_index
        with patch("src.services.whatsapp.storage.get_conn", side_effect=Exception("db error")):
            assert get_recent_chats_from_index() == []


class TestAddMessageToHistory:
    async def test_creates_new_history_file(self, tmp_path):
        chats_dir = tmp_path / "chats"
        chats_dir.mkdir()
        with patch("src.services.whatsapp.storage._chats_dir", return_value=chats_dir):
            from src.services.whatsapp.storage import add_message_to_history
            await add_message_to_history("5511999999999", {"key": {"id": "msg_1"}, "message": {"conversation": "Hi"}})
            file_path = chats_dir / "5511999999999.json.gz"
            assert file_path.exists()

    async def test_appends_to_existing_history(self, tmp_path):
        chats_dir = tmp_path / "chats"
        chats_dir.mkdir()
        with patch("src.services.whatsapp.storage._chats_dir", return_value=chats_dir):
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
        with patch("src.services.whatsapp.storage._chats_dir", return_value=chats_dir):
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
        with patch("src.services.whatsapp.storage._chats_dir", return_value=chats_dir):
            with patch("src.services.whatsapp.storage.HISTORY_LIMIT", 3):
                from src.services.whatsapp.storage import add_message_to_history
                for i in range(10):
                    await add_message_to_history("5511999999999", {"key": {"id": f"msg_{i}"}})
                import gzip
                file_path = chats_dir / "5511999999999.json.gz"
                data = json.loads(gzip.open(file_path, "rt").read())
                assert len(data) == 3

    async def test_handles_empty_phone(self, tmp_path):
        chats_dir = tmp_path / "chats"
        chats_dir.mkdir()
        with patch("src.services.whatsapp.storage._chats_dir", return_value=chats_dir):
            from src.services.whatsapp.storage import add_message_to_history
            await add_message_to_history("", {"key": {"id": "msg_1"}})
            assert len(list(chats_dir.iterdir())) == 0

    async def test_handles_exception_gracefully(self):
        with patch("gzip.open", side_effect=Exception("io error")):
            with patch("src.services.whatsapp.storage._chats_dir", return_value=__import__("pathlib").Path("/nonexistent")):
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
        with patch("src.services.whatsapp.storage._chats_dir", return_value=chats_dir):
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
        with patch("src.services.whatsapp.storage._chats_dir", return_value=chats_dir):
            from src.services.whatsapp.storage import get_history
            result = await get_history("5511999999999")
            assert result == expected

    async def test_handles_exception_returns_empty(self, tmp_path):
        chats_dir = tmp_path / "chats"
        chats_dir.mkdir()
        with patch("src.services.whatsapp.storage._chats_dir", return_value=chats_dir):
            from src.services.whatsapp.storage import get_history
            with patch("gzip.open", side_effect=Exception("read error")):
                result = await get_history("5511999999999")
                assert result == []


class TestClearAllData:
    async def test_clears_gzip_files(self, tmp_path):
        chats_dir = tmp_path / "chats"
        chats_dir.mkdir()
        (chats_dir / "a.json.gz").write_text("a")
        (chats_dir / "b.json.gz").write_text("b")
        with patch("src.services.whatsapp.storage._chats_dir", return_value=chats_dir):
            from src.services.whatsapp.storage import clear_all_data
            await clear_all_data()
            assert len(list(chats_dir.iterdir())) == 0

    async def test_clears_chat_index_from_db(self, tmp_path):
        chats_dir = tmp_path / "chats"
        chats_dir.mkdir()
        from src.services.whatsapp.storage import save_chat_index, get_recent_chats_from_index, clear_all_data
        await save_chat_index({"id": "test@s.whatsapp.net", "name": "Test"})
        assert len(get_recent_chats_from_index()) == 1
        with patch("src.services.whatsapp.storage._chats_dir", return_value=chats_dir):
            await clear_all_data()
        assert get_recent_chats_from_index() == []

    async def test_handles_nonexistent_dir(self, tmp_path):
        chats_dir = tmp_path / "nonexistent"
        with patch("src.services.whatsapp.storage._chats_dir", return_value=chats_dir):
            from src.services.whatsapp.storage import clear_all_data
            await clear_all_data()  # should not raise
