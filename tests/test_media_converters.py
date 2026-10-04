from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestImageConverter:
    async def test_convert_to_webp_success(self, tmp_path):
        input_file = tmp_path / "test.jpg"
        input_file.write_text("fake image data")
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("src.services.media.imageConverter.run_ffmpeg_sync", return_value=mock_result):
            from src.services.media.imageConverter import convert_to_webp
            result = await convert_to_webp(str(input_file))
            assert "_conv.webp" in result

    async def test_convert_to_webp_failure(self, tmp_path):
        input_file = tmp_path / "test.jpg"
        input_file.write_text("fake image data")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = b"ffmpeg error"
        with patch("src.services.media.imageConverter.run_ffmpeg_sync", return_value=mock_result):
            from src.services.media.imageConverter import convert_to_webp
            with pytest.raises(Exception, match="ffmpeg error"):
                await convert_to_webp(str(input_file))

    async def test_convert_to_webp_stretch_mode(self, tmp_path):
        input_file = tmp_path / "test.jpg"
        input_file.write_text("fake")
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("src.services.media.imageConverter.run_ffmpeg_sync", return_value=mock_result):
            from src.services.media.imageConverter import convert_to_webp
            with patch("src.services.media.imageConverter.logger.debug") as mock_debug:
                await convert_to_webp(str(input_file), {"resizeMode": "stretch"})
                cmd_str = mock_debug.call_args[0][0]
                assert "scale=512:512" in cmd_str

    async def test_convert_to_webp_cover_mode(self, tmp_path):
        input_file = tmp_path / "test.jpg"
        input_file.write_text("fake")
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("src.services.media.imageConverter.run_ffmpeg_sync", return_value=mock_result):
            from src.services.media.imageConverter import convert_to_webp
            with patch("src.services.media.imageConverter.logger.debug") as mock_debug:
                await convert_to_webp(str(input_file), {"resizeMode": "cover"})
                cmd_str = mock_debug.call_args[0][0]
                assert "crop=512:512" in cmd_str

    async def test_convert_to_webp_pad_mode(self, tmp_path):
        input_file = tmp_path / "test.jpg"
        input_file.write_text("fake")
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("src.services.media.imageConverter.run_ffmpeg_sync", return_value=mock_result):
            from src.services.media.imageConverter import convert_to_webp
            with patch("src.services.media.imageConverter.logger.debug") as mock_debug:
                await convert_to_webp(str(input_file), {"resizeMode": "pad", "padColor": "red"})
                cmd_str = mock_debug.call_args[0][0]
                assert "color=red" in cmd_str

    async def test_convert_to_webp_blur_mode(self, tmp_path):
        input_file = tmp_path / "test.jpg"
        input_file.write_text("fake")
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("src.services.media.imageConverter.run_ffmpeg_sync", return_value=mock_result):
            from src.services.media.imageConverter import convert_to_webp
            with patch("src.services.media.imageConverter.logger.debug") as mock_debug:
                await convert_to_webp(str(input_file), {"resizeMode": "blur", "blurIntensity": 30})
                cmd_str = mock_debug.call_args[0][0]
                assert "boxblur=30" in cmd_str

    async def test_convert_to_webp_transparent_mode(self, tmp_path):
        input_file = tmp_path / "test.jpg"
        input_file.write_text("fake")
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("src.services.media.imageConverter.run_ffmpeg_sync", return_value=mock_result):
            from src.services.media.imageConverter import convert_to_webp
            with patch("src.services.media.imageConverter.logger.debug") as mock_debug:
                await convert_to_webp(str(input_file), {"resizeMode": "transparent"})
                cmd_str = mock_debug.call_args[0][0]
                assert "rgba" in cmd_str

    async def test_convert_to_webp_default_options(self, tmp_path):
        input_file = tmp_path / "test.jpg"
        input_file.write_text("fake")
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("src.services.media.imageConverter.run_ffmpeg_sync", return_value=mock_result):
            from src.services.media.imageConverter import convert_to_webp
            await convert_to_webp(str(input_file))  # should not raise

    async def test_convert_to_webp_exception_handling(self, tmp_path):
        input_file = tmp_path / "test.jpg"
        input_file.write_text("fake")
        with patch("src.services.media.imageConverter.run_ffmpeg_sync", side_effect=Exception("subprocess failed")):
            from src.services.media.imageConverter import convert_to_webp
            with pytest.raises(Exception, match="subprocess failed"):
                await convert_to_webp(str(input_file))


class TestVideoConverter:
    async def test_convert_to_mp4_success(self, tmp_path):
        input_file = tmp_path / "test.mkv"
        input_file.write_text("fake video")
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("src.services.media.videoConverter.run_ffmpeg_sync", return_value=mock_result):
            from src.services.media.videoConverter import convert_to_mp4
            result = await convert_to_mp4(str(input_file))
            assert "_conv.mp4" in result

    async def test_convert_to_mp4_failure(self, tmp_path):
        input_file = tmp_path / "test.mkv"
        input_file.write_text("fake")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = b"conversion error"
        with patch("src.services.media.videoConverter.run_ffmpeg_sync", return_value=mock_result):
            from src.services.media.videoConverter import convert_to_mp4
            with pytest.raises(Exception, match="conversion error"):
                await convert_to_mp4(str(input_file))


class TestAudioConverter:
    async def test_convert_to_ogg_success(self, tmp_path):
        input_file = tmp_path / "test.wav"
        input_file.write_text("fake audio")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = b""
        with patch("src.services.media.audioConverter.run_ffmpeg_sync", return_value=mock_result):
            from src.services.media.audioConverter import convert_audio
            result_path, duration = await convert_audio(str(input_file), "ogg")
            assert ".ogg" in result_path

    async def test_convert_to_mp3_success(self, tmp_path):
        input_file = tmp_path / "test.wav"
        input_file.write_text("fake audio")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = b""
        with patch("src.services.media.audioConverter.run_ffmpeg_sync", return_value=mock_result):
            from src.services.media.audioConverter import convert_audio
            result_path, duration = await convert_audio(str(input_file), "mp3")
            assert ".mp3" in result_path

    async def test_convert_to_wav_success(self, tmp_path):
        input_file = tmp_path / "test.ogg"
        input_file.write_text("fake audio")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = b""
        with patch("src.services.media.audioConverter.run_ffmpeg_sync", return_value=mock_result):
            from src.services.media.audioConverter import convert_audio
            result_path, duration = await convert_audio(str(input_file), "wav")
            assert ".wav" in result_path

    async def test_convert_to_m4a_success(self, tmp_path):
        input_file = tmp_path / "test.ogg"
        input_file.write_text("fake audio")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = b""
        with patch("src.services.media.audioConverter.run_ffmpeg_sync", return_value=mock_result):
            from src.services.media.audioConverter import convert_audio
            result_path, duration = await convert_audio(str(input_file), "m4a")
            assert ".m4a" in result_path

    async def test_invalid_format_raises(self, tmp_path):
        input_file = tmp_path / "test.ogg"
        input_file.write_text("fake")
        from src.services.media.audioConverter import convert_audio
        with pytest.raises(ValueError, match="Unsupported format"):
            await convert_audio(str(input_file), "flac")

    async def test_ffmpeg_error_raises(self, tmp_path):
        input_file = tmp_path / "test.wav"
        input_file.write_text("fake")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = b"encode error"
        with patch("src.services.media.audioConverter.run_ffmpeg_sync", return_value=mock_result):
            from src.services.media.audioConverter import convert_audio
            with pytest.raises(Exception, match="encode error"):
                await convert_audio(str(input_file), "ogg")

    async def test_duration_extraction(self, tmp_path):
        input_file = tmp_path / "test.ogg"
        input_file.write_text("fake audio")
        output_file = tmp_path / "test.ogg"

        def run_side_effect(cmd):
            result = MagicMock()
            if len(cmd) == 3:  # probe: ["ffmpeg", "-i", filepath]
                result.returncode = 0
                result.stderr = b"Duration: 00:01:30.50, start: 0.000000, bitrate: 64 kb/s"
            else:
                result.returncode = 0
                result.stderr = b""
            return result

        with patch("src.services.media.audioConverter.run_ffmpeg_sync", side_effect=run_side_effect):
            from src.services.media.audioConverter import convert_audio
            result_path, duration = await convert_audio(str(input_file), "ogg")
            assert duration == 90




class TestEmbedStickerExif:
    @staticmethod
    def _animated_webp(path):
        from PIL import Image
        frames = [Image.new("RGB", (32, 32), c) for c in ("red", "blue")]
        frames[0].save(path, format="webp", save_all=True, append_images=frames[1:], duration=100, loop=0)

    def test_writes_pack_and_author_keeping_animation(self, tmp_path):
        from PIL import Image
        from src.services.media.imageConverter import embed_sticker_exif
        f = tmp_path / "a.webp"
        self._animated_webp(f)
        assert embed_sticker_exif(str(f), "My Pack", "My Author") is True
        img = Image.open(f)
        assert img.n_frames == 2
        exif = img.info["exif"].decode("utf-8", "ignore")
        assert '"sticker-pack-name": "My Pack"' in exif
        assert '"sticker-pack-publisher": "My Author"' in exif

    def test_replaces_existing_exif(self, tmp_path):
        from PIL import Image
        from src.services.media.imageConverter import embed_sticker_exif
        f = tmp_path / "a.webp"
        self._animated_webp(f)
        embed_sticker_exif(str(f), "One", "A")
        embed_sticker_exif(str(f), "Two", "B")
        exif = Image.open(f).info["exif"].decode("utf-8", "ignore")
        assert "Two" in exif and "One" not in exif

    def test_noop_without_metadata(self, tmp_path):
        from src.services.media.imageConverter import embed_sticker_exif
        f = tmp_path / "a.webp"
        self._animated_webp(f)
        before = f.read_bytes()
        assert embed_sticker_exif(str(f), "", "") is False
        assert f.read_bytes() == before

    def test_rejects_non_webp(self, tmp_path):
        from src.services.media.imageConverter import embed_sticker_exif
        f = tmp_path / "a.webp"
        f.write_bytes(b"not a webp")
        assert embed_sticker_exif(str(f), "x", "y") is False
