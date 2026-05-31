"""Tests for the URL builder module."""

from unittest.mock import patch

from src.config.url_builder import build_qr_url


class TestBuildQrUrl:
    """Test build_qr_url under various environment conditions."""

    @patch("src.config.url_builder.os.getenv")
    def test_with_public_url(self, mock_getenv):
        def mock_getenv_side_effect(key, default=None):
            env = {
                "PUBLIC_URL": "https://myapp.example.com",
                "USER": None,
            }
            return env.get(key, default)
        mock_getenv.side_effect = mock_getenv_side_effect

        result = build_qr_url()
        assert result.startswith("https://myapp.example.com:8300/qr")

    @patch("src.config.url_builder.os.getenv")
    def test_with_public_url_already_has_port(self, mock_getenv):
        def mock_getenv_side_effect(key, default=None):
            env = {
                "PUBLIC_URL": "https://myapp.example.com:9000",
                "USER": None,
            }
            return env.get(key, default)
        mock_getenv.side_effect = mock_getenv_side_effect

        result = build_qr_url()
        assert "myapp.example.com:9000" in result
        assert "/qr" in result

    @patch("src.config.url_builder.os.getenv")
    @patch("src.config.url_builder.socket.gethostname")
    def test_fallback_to_hostname(self, mock_hostname, mock_getenv):
        def mock_getenv_side_effect(key, default=None):
            env = {"PUBLIC_URL": None, "USER": None}
            return env.get(key, default)
        mock_getenv.side_effect = mock_getenv_side_effect
        mock_hostname.return_value = "myserver"

        result = build_qr_url()
        assert "myserver" in result
        assert ":8300" in result

    @patch("src.config.url_builder.os.getenv")
    def test_with_api_key(self, mock_getenv):
        def mock_getenv_side_effect(key, default=None):
            from src.config.constants import API_KEY
            env = {
                "PUBLIC_URL": "https://app.example.com",
                "USER": None,
            }
            return env.get(key, default)
        mock_getenv.side_effect = mock_getenv_side_effect

        with patch("src.config.url_builder.API_KEY", "my-secret-key"):
            result = build_qr_url()
            assert "API_KEY=my-secret-key" in result
