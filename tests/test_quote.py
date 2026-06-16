"""Tests for src/utils/quote.py — resolve_quote(), build_send_options()."""

import pytest
from unittest.mock import AsyncMock, patch

from src.utils.quote import build_send_options, resolve_quote


FOUND_MSG = {"key": {"remoteJid": "5511@s.whatsapp.net", "id": "msg1"}, "message": {"conversation": "hi"}}


class TestResolveQuote:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_identifier(self):
        result = await resolve_quote("jid@s.whatsapp.net", None)
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_when_identifier_is_empty_string(self):
        result = await resolve_quote("jid@s.whatsapp.net", "")
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_quoted_when_found(self):
        with patch("src.utils.quote.find_message", new=AsyncMock(return_value=FOUND_MSG)):
            result = await resolve_quote("jid@s.whatsapp.net", "msg1", "id")
        assert result == {"quoted": FOUND_MSG}

    @pytest.mark.asyncio
    async def test_returns_stub_when_id_not_found(self):
        with patch("src.utils.quote.find_message", new=AsyncMock(return_value=None)):
            result = await resolve_quote("5511@s.whatsapp.net", "ghost-id", "id")
        assert "quoted" in result
        assert result["quoted"]["key"]["id"] == "ghost-id"
        assert result["quoted"]["key"]["remoteJid"] == "5511@s.whatsapp.net"

    @pytest.mark.asyncio
    async def test_raises_when_text_not_found(self):
        with patch("src.utils.quote.find_message", new=AsyncMock(return_value=None)):
            with pytest.raises(Exception, match="Could not find the message"):
                await resolve_quote("jid@s.whatsapp.net", "missing text", "text")

    @pytest.mark.asyncio
    async def test_returns_quoted_when_text_found(self):
        with patch("src.utils.quote.find_message", new=AsyncMock(return_value=FOUND_MSG)):
            result = await resolve_quote("jid@s.whatsapp.net", "hi", "text")
        assert result == {"quoted": FOUND_MSG}


class TestBuildSendOptions:
    @pytest.mark.asyncio
    async def test_empty_options_when_no_params(self):
        with patch("src.utils.quote.find_message", new=AsyncMock(return_value=None)):
            result = await build_send_options("jid@s.whatsapp.net")
        assert result == {}

    @pytest.mark.asyncio
    async def test_includes_delay_message(self):
        with patch("src.utils.quote.find_message", new=AsyncMock(return_value=None)):
            result = await build_send_options("jid@s.whatsapp.net", delay_message=500)
        assert result["delay_message"] == 500

    @pytest.mark.asyncio
    async def test_includes_delay_typing(self):
        with patch("src.utils.quote.find_message", new=AsyncMock(return_value=None)):
            result = await build_send_options("jid@s.whatsapp.net", delay_typing=1.5)
        assert result["delay_typing"] == 1.5

    @pytest.mark.asyncio
    async def test_includes_mentioned(self):
        with patch("src.utils.quote.find_message", new=AsyncMock(return_value=None)):
            result = await build_send_options(
                "jid@s.whatsapp.net", mentioned=["5511@s.whatsapp.net"]
            )
        assert result["mentioned"] == ["5511@s.whatsapp.net"]

    @pytest.mark.asyncio
    async def test_excludes_delay_message_when_none(self):
        with patch("src.utils.quote.find_message", new=AsyncMock(return_value=None)):
            result = await build_send_options("jid@s.whatsapp.net", delay_message=None)
        assert "delay_message" not in result

    @pytest.mark.asyncio
    async def test_excludes_mentioned_when_empty(self):
        with patch("src.utils.quote.find_message", new=AsyncMock(return_value=None)):
            result = await build_send_options("jid@s.whatsapp.net", mentioned=[])
        assert "mentioned" not in result

    @pytest.mark.asyncio
    async def test_all_options_combined(self):
        with patch("src.utils.quote.find_message", new=AsyncMock(return_value=FOUND_MSG)):
            result = await build_send_options(
                "jid@s.whatsapp.net",
                reply_identifier="msg1",
                delay_message=200,
                delay_typing=0.5,
                mentioned=["a@s.whatsapp.net"],
            )
        assert "quoted" in result
        assert result["delay_message"] == 200
        assert result["delay_typing"] == 0.5
        assert result["mentioned"] == ["a@s.whatsapp.net"]
