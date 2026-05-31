"""Tests for the pairing service."""

from unittest.mock import patch, MagicMock

import pytest
from fastapi import HTTPException

from src.services.whatsapp.pairing_service import generate_pairing_code, _sanitize_phone


class TestSanitizePhone:
    """Test the _sanitize_phone helper."""

    def test_removes_non_digits(self):
        assert _sanitize_phone("+55 (11) 99999-9999") == "5511999999999"

    def test_passes_through_digits_only(self):
        assert _sanitize_phone("5511999999999") == "5511999999999"

    def test_empty_string(self):
        assert _sanitize_phone("") == ""

    def test_only_non_digits(self):
        assert _sanitize_phone("abc-()") == ""


@pytest.mark.asyncio
class TestGeneratePairingCode:
    """Test generate_pairing_code with mocked dependencies."""

    @patch("src.services.whatsapp.pairing_service.get_is_ready")
    async def test_raises_if_already_connected(self, mock_get_is_ready):
        mock_get_is_ready.return_value = True
        with pytest.raises(HTTPException) as exc:
            await generate_pairing_code("5511999999999")
        assert exc.value.status_code == 409
        assert "WHATSAPP_ALREADY_CONNECTED" in str(exc.value.detail)

    @patch("src.services.whatsapp.pairing_service.get_is_ready")
    @patch("src.services.whatsapp.pairing_service.get_client")
    async def test_raises_if_no_client(self, mock_get_client, mock_get_is_ready):
        mock_get_is_ready.return_value = False
        mock_get_client.return_value = None
        with pytest.raises(HTTPException) as exc:
            await generate_pairing_code("5511999999999")
        assert exc.value.status_code == 503

    @patch("src.services.whatsapp.pairing_service.get_is_ready")
    @patch("src.services.whatsapp.pairing_service.get_client")
    async def test_raises_if_empty_phone(self, mock_get_client, mock_get_is_ready):
        mock_get_is_ready.return_value = False
        mock_get_client.return_value = MagicMock()
        with pytest.raises(HTTPException) as exc:
            await generate_pairing_code("")
        assert exc.value.status_code == 400
        assert "MISSING_FIELD" in str(exc.value.detail)

    @patch("src.services.whatsapp.pairing_service.get_is_ready")
    @patch("src.services.whatsapp.pairing_service.get_client")
    async def test_raises_if_pair_returns_none(self, mock_get_client, mock_get_is_ready):
        mock_get_is_ready.return_value = False
        mock_sock = MagicMock()
        mock_sock.PairPhone.return_value = None
        mock_get_client.return_value = mock_sock
        with pytest.raises(HTTPException) as exc:
            await generate_pairing_code("5511999999999")
        assert exc.value.status_code == 500
        assert "PAIR_FAILED" in str(exc.value.detail)

    @patch("src.services.whatsapp.pairing_service.get_is_ready")
    @patch("src.services.whatsapp.pairing_service.get_client")
    async def test_raises_if_pair_returns_non_string(self, mock_get_client, mock_get_is_ready):
        mock_get_is_ready.return_value = False
        mock_sock = MagicMock()
        mock_sock.PairPhone.return_value = 12345
        mock_get_client.return_value = mock_sock
        with pytest.raises(HTTPException) as exc:
            await generate_pairing_code("5511999999999")
        assert exc.value.status_code == 500

    @patch("src.services.whatsapp.pairing_service.get_is_ready")
    @patch("src.services.whatsapp.pairing_service.get_client")
    async def test_success(self, mock_get_client, mock_get_is_ready):
        mock_get_is_ready.return_value = False
        mock_sock = MagicMock()
        mock_sock.PairPhone.return_value = "ABCD-1234"
        mock_get_client.return_value = mock_sock
        result = await generate_pairing_code("5511999999999")
        assert result == "ABCD-1234"
