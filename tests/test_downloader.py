from unittest.mock import MagicMock, patch

import pytest


class TestDownloadMedia:
    @patch("src.services.media.downloader.TEMP_DIR", "/tmp")
    def test_raises_on_invalid_protocol(self):
        from src.services.media.downloader import download_media
        with pytest.raises(Exception, match="Invalid protocol"):
            import asyncio
            asyncio.run(download_media("ftp://files.example.com/test.mp4"))

    @patch("src.services.media.downloader.TEMP_DIR", "/tmp")
    def test_raises_on_missing_hostname(self):
        from src.services.media.downloader import download_media
        with pytest.raises(Exception, match="hostname not identified"):
            import asyncio
            asyncio.run(download_media("http:///path"))

    @patch("src.services.media.downloader.TEMP_DIR", "/tmp")
    def test_blocks_private_ip(self):
        from src.services.media.downloader import download_media
        with patch("socket.gethostbyname", return_value="127.0.0.1"):
            with pytest.raises(Exception, match="protected/internal IP"):
                import asyncio
                asyncio.run(download_media("http://localhost/test.mp4"))

    @patch("src.services.media.downloader.TEMP_DIR", "/tmp")
    def test_blocks_link_local_ip(self):
        from src.services.media.downloader import download_media
        with patch("socket.gethostbyname", return_value="169.254.1.1"):
            with pytest.raises(Exception, match="protected/internal IP"):
                import asyncio
                asyncio.run(download_media("http://example.com/test.mp4"))

    @patch("src.services.media.downloader.TEMP_DIR", "/tmp")
    def test_blocks_multicast_ip(self):
        from src.services.media.downloader import download_media
        with patch("socket.gethostbyname", return_value="224.0.0.1"):
            with pytest.raises(Exception, match="protected/internal IP"):
                import asyncio
                asyncio.run(download_media("http://example.com/test.mp4"))

    @patch("src.services.media.downloader.TEMP_DIR", "/tmp")
    def test_successful_download(self, tmp_path):
        from src.services.media.downloader import download_media
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "image/jpeg", "content-length": "1024"}
        mock_response.iter_content.return_value = [b"data"]
        mock_response.__enter__.return_value = mock_response
        mock_response.raise_for_status.return_value = None

        with patch("socket.gethostbyname", return_value="93.184.216.34"):
            with patch("requests.get", return_value=mock_response):
                with patch("src.services.media.downloader.TEMP_DIR", str(tmp_path)):
                    result = download_media("http://example.com/photo.jpg")
                    import asyncio
                    result = asyncio.run(result)
                    assert "jpg" in result

    @patch("src.services.media.downloader.TEMP_DIR", "/tmp")
    def test_blocks_large_file(self, tmp_path):
        from src.services.media.downloader import download_media
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "video/mp4", "content-length": str(500 * 1024 * 1024)}
        mock_response.__enter__.return_value = mock_response
        mock_response.raise_for_status.return_value = None

        with patch("socket.gethostbyname", return_value="93.184.216.34"):
            with patch("requests.get", return_value=mock_response):
                with patch("src.services.media.downloader.TEMP_DIR", str(tmp_path)):
                    result = download_media("http://example.com/big.mp4")
                    import asyncio
                    with pytest.raises(Exception, match="File too large"):
                        asyncio.run(result)

    @patch("src.services.media.downloader.TEMP_DIR", "/tmp")
    def test_detects_extension_from_content_type(self, tmp_path):
        from src.services.media.downloader import download_media
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/pdf", "content-length": "500"}
        mock_response.iter_content.return_value = [b"pdf data"]
        mock_response.__enter__.return_value = mock_response
        mock_response.raise_for_status.return_value = None

        with patch("socket.gethostbyname", return_value="93.184.216.34"):
            with patch("requests.get", return_value=mock_response):
                with patch("src.services.media.downloader.TEMP_DIR", str(tmp_path)):
                    result = download_media("http://example.com/doc")
                    import asyncio
                    result = asyncio.run(result)
                    assert result.endswith(".pdf")

    @patch("src.services.media.downloader.TEMP_DIR", "/tmp")
    def test_fallback_extension(self, tmp_path):
        from src.services.media.downloader import download_media
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/octet-stream", "content-length": "500"}
        mock_response.iter_content.return_value = [b"binary data"]
        mock_response.__enter__.return_value = mock_response
        mock_response.raise_for_status.return_value = None

        with patch("socket.gethostbyname", return_value="93.184.216.34"):
            with patch("requests.get", return_value=mock_response):
                with patch("src.services.media.downloader.TEMP_DIR", str(tmp_path)):
                    result = download_media("http://example.com/file")
                    import asyncio
                    result = asyncio.run(result)
                    assert result.endswith(".bin")
