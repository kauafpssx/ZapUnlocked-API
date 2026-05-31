"""Tests for FFmpeg path resolution and media utility functions."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.services.media.utils import (
    get_ffmpeg_path,
    warm_up_ffmpeg,
    run_ffmpeg_sync,
    cleanup,
    get_file_size,
)


class TestGetFfmpegPath:
    def test_uses_imageio_when_available(self):
        mock_imageio = MagicMock()
        mock_imageio.get_ffmpeg_exe.return_value = "/usr/bin/ffmpeg"
        with patch.dict("sys.modules", {"imageio_ffmpeg": mock_imageio}):
            from src.services.media import utils
            utils._ffmpeg_path = None
            result = get_ffmpeg_path()
            assert result == "/usr/bin/ffmpeg"

    def test_uses_shutil_when_imageio_unavailable(self):
        with patch.dict("sys.modules", {"imageio_ffmpeg": None}):
            with patch("src.services.media.utils.shutil.which", return_value="/usr/local/bin/ffmpeg"):
                from src.services.media import utils
                utils._ffmpeg_path = None
                result = get_ffmpeg_path()
                assert result == "/usr/local/bin/ffmpeg"

    def test_uses_home_local_bin(self):
        with patch.dict("sys.modules", {"imageio_ffmpeg": None}):
            with patch("src.services.media.utils.shutil.which", return_value=None):
                with patch("src.services.media.utils.Path.home") as mock_home:
                    mock_home.return_value = Path("/home/user")
                    with patch("src.services.media.utils.Path.exists") as mock_exists:
                        mock_exists.return_value = True
                        from src.services.media import utils
                        utils._ffmpeg_path = None
                        result = get_ffmpeg_path()
                        assert "ffmpeg" in result

    def test_raises_when_not_found(self):
        with patch.dict("sys.modules", {"imageio_ffmpeg": None}):
            with patch("src.services.media.utils.shutil.which", return_value=None):
                with patch("src.services.media.utils.Path.exists") as mock_exists:
                    mock_exists.return_value = False
                    from src.services.media import utils
                    utils._ffmpeg_path = None
                    with pytest.raises(FileNotFoundError, match="ffmpeg not found"):
                        get_ffmpeg_path()

    def test_caches_result(self):
        from src.services.media import utils
        utils._ffmpeg_path = "/cached/ffmpeg"
        result = get_ffmpeg_path()
        assert result == "/cached/ffmpeg"



class TestWarmUpFfmpeg:
    def test_logs_path_when_found(self):
        with patch("src.services.media.utils.get_ffmpeg_path", return_value="/usr/bin/ffmpeg"):
            with patch("src.services.media.utils.logger.info") as mock_log:
                warm_up_ffmpeg()
                mock_log.assert_called_once()

    def test_logs_warning_when_not_found(self):
        with patch("src.services.media.utils.get_ffmpeg_path", side_effect=FileNotFoundError("not found")):
            with patch("src.services.media.utils.logger.warning") as mock_log:
                warm_up_ffmpeg()
                mock_log.assert_called_once()


class TestRunFfmpegSync:
    def test_replaces_ffmpeg_with_full_path(self):
        with patch("src.services.media.utils.get_ffmpeg_path", return_value="/usr/bin/ffmpeg"):
            with patch("src.services.media.utils.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock()
                run_ffmpeg_sync(["ffmpeg", "-i", "input.mp4"])
                cmd_used = mock_run.call_args[0][0]
                assert cmd_used[0] == "/usr/bin/ffmpeg"

    def test_passes_through_non_ffmpeg_command(self):
        with patch("src.services.media.utils.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock()
            run_ffmpeg_sync(["echo", "hello"])
            cmd_used = mock_run.call_args[0][0]
            assert cmd_used[0] == "echo"


class TestCleanup:
    def test_removes_existing_file(self, tmp_path):
        test_file = tmp_path / "temp.txt"
        test_file.write_text("data")
        cleanup(str(test_file))
        assert not test_file.exists()

    def test_does_nothing_for_nonexistent_file(self, tmp_path):
        test_file = tmp_path / "nonexistent.txt"
        cleanup(str(test_file))

    def test_does_nothing_for_empty_path(self):
        cleanup("")


class TestGetFileSize:
    def test_returns_size_for_existing_file(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        size = get_file_size(str(test_file))
        assert size == 5

    def test_returns_zero_for_nonexistent(self, tmp_path):
        size = get_file_size(str(tmp_path / "nope.txt"))
        assert size == 0
