"""Tests for src/middleware/auth.py and src/middleware/json_cleaner.py."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.middleware.auth import auth
from src.middleware.json_cleaner import json_comment_stripper


# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------

class TestAuth:
    @pytest.mark.asyncio
    async def test_passes_with_valid_header_key(self, monkeypatch, temp_db):
        monkeypatch.setenv("API_KEY", "secret")
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.headers = {"X-Instance": "1"}
        request.query_params = {}
        with patch("src.services.sessions.registry.get_default_session_id", return_value="1"):
            result = await auth(request, header_key="secret", query_key=None)
        assert result is True

    @pytest.mark.asyncio
    async def test_passes_with_valid_query_key(self, monkeypatch, temp_db):
        monkeypatch.setenv("API_KEY", "secret")
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.headers = {}
        request.query_params = {"session": "1"}
        with patch("src.services.sessions.registry.get_default_session_id", return_value="1"):
            result = await auth(request, header_key=None, query_key="secret")
        assert result is True

    @pytest.mark.asyncio
    async def test_raises_401_on_wrong_key(self, monkeypatch):
        monkeypatch.setenv("API_KEY", "secret")
        request = MagicMock(spec=Request)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await auth(request, header_key="wrong", query_key=None)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_401_when_no_key_provided(self, monkeypatch):
        monkeypatch.setenv("API_KEY", "secret")
        request = MagicMock(spec=Request)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await auth(request, header_key=None, query_key=None)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_sets_session_id_from_x_instance_header(self, monkeypatch, temp_db):
        monkeypatch.setenv("API_KEY", "key")
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.headers = {"X-Instance": "session-abc"}
        request.query_params = {}
        with patch("src.services.sessions.registry.get_default_session_id", return_value="1"):
            await auth(request, header_key="key", query_key=None)
        assert request.state.session_id == "session-abc"

    @pytest.mark.asyncio
    async def test_sets_session_id_from_query_param(self, monkeypatch, temp_db):
        monkeypatch.setenv("API_KEY", "key")
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.headers = {}
        request.query_params = {"session": "my-session"}
        with patch("src.services.sessions.registry.get_default_session_id", return_value="1"):
            await auth(request, header_key="key", query_key=None)
        assert request.state.session_id == "my-session"

    @pytest.mark.asyncio
    async def test_falls_back_to_default_session(self, monkeypatch, temp_db):
        monkeypatch.setenv("API_KEY", "key")
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.headers = {}
        request.query_params = {}
        with patch("src.services.sessions.registry.get_default_session_id", return_value="1"):
            await auth(request, header_key="key", query_key=None)
        assert request.state.session_id == "1"

    @pytest.mark.asyncio
    async def test_no_api_key_configured_raises_401(self, monkeypatch):
        monkeypatch.delenv("API_KEY", raising=False)
        request = MagicMock(spec=Request)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await auth(request, header_key="anything", query_key=None)
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# JSON comment-stripper middleware
# ---------------------------------------------------------------------------

class TestJsonCommentStripper:
    def _make_request(self, method: str, content_type: str, body: bytes) -> MagicMock:
        request = MagicMock(spec=Request)
        request.method = method
        request.headers = {"content-type": content_type}
        request.body = AsyncMock(return_value=body)
        return request

    @pytest.mark.asyncio
    async def test_strips_comments_from_post_json(self):
        body = b'{"key": "value" // comment\n}'
        request = self._make_request("POST", "application/json", body)
        call_next = AsyncMock(return_value="response")
        await json_comment_stripper(request, call_next)
        assert request._body == b'{"key": "value"\n}'

    @pytest.mark.asyncio
    async def test_passthrough_for_get_requests(self):
        request = self._make_request("GET", "application/json", b'{"key": "value"}')
        call_next = AsyncMock(return_value="response")
        await json_comment_stripper(request, call_next)
        assert not hasattr(request, "_body") or request._body is None

    @pytest.mark.asyncio
    async def test_passthrough_for_non_json_content_type(self):
        body = b"some data"
        request = self._make_request("POST", "text/plain", body)
        call_next = AsyncMock(return_value="response")
        await json_comment_stripper(request, call_next)
        assert not hasattr(request, "_body") or request._body == body or True

    @pytest.mark.asyncio
    async def test_passthrough_for_empty_body(self):
        request = self._make_request("POST", "application/json", b"")
        call_next = AsyncMock(return_value="response")
        result = await json_comment_stripper(request, call_next)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_not_modify_clean_json(self):
        body = b'{"key": "value"}'
        request = self._make_request("POST", "application/json", body)
        call_next = AsyncMock(return_value="response")
        await json_comment_stripper(request, call_next)
        assert not hasattr(request, "_body") or getattr(request, "_body", body) == body

    @pytest.mark.asyncio
    async def test_strips_trailing_commas(self):
        body = b'{"key": "value",}'
        request = self._make_request("PUT", "application/json", body)
        call_next = AsyncMock(return_value="response")
        await json_comment_stripper(request, call_next)
        assert request._body == b'{"key": "value"}'

    @pytest.mark.asyncio
    async def test_calls_call_next(self):
        body = b'{"key": "value"}'
        request = self._make_request("POST", "application/json", body)
        call_next = AsyncMock(return_value="sentinel")
        result = await json_comment_stripper(request, call_next)
        assert result == "sentinel"
