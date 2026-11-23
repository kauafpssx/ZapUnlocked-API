import asyncio

from src.controllers.status import logsController


def test_delete_all_logs_removes_archives_and_truncates_active(tmp_path, monkeypatch):
    active = tmp_path / "zapunlocked_2026-11-23.log"
    archive = tmp_path / "zapunlocked_2026-11-22.log.gz"
    active.write_text("secret log", encoding="utf-8")
    archive.write_bytes(b"archive")
    monkeypatch.setattr(logsController, "_LOG_DIR", tmp_path)

    result = asyncio.run(logsController.delete_all_logs())

    assert result["deleted"] == 1
    assert result["truncated"] == 1
    assert active.exists()
    assert active.read_text(encoding="utf-8") == ""
    assert not archive.exists()
