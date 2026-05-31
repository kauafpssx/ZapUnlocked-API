"""Tests for reusable FastAPI decorators."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.utils.decorators import require_whatsapp, handle_errors


@pytest.fixture(autouse=True)
def mock_get_is_ready():
    """Patch get_is_ready which is imported lazily inside require_whatsapp."""
    with patch("src.services.whatsapp.client.get_is_ready") as mock:
        yield mock


class TestRequireWhatsapp:
    async def test_passes_when_ready(self, mock_get_is_ready):
        mock_get_is_ready.return_value = True
        mock_fn = AsyncMock(return_value="ok")

        decorated = require_whatsapp(mock_fn)
        result = await decorated()
        assert result == "ok"
        mock_fn.assert_awaited_once()

    async def test_raises_503_when_not_ready(self, mock_get_is_ready):
        mock_get_is_ready.return_value = False
        mock_fn = AsyncMock()

        decorated = require_whatsapp(mock_fn)
        with pytest.raises(HTTPException) as exc:
            await decorated()
        assert exc.value.status_code == 503
        assert "WHATSAPP_NOT_CONNECTED" in str(exc.value.detail)
        mock_fn.assert_not_awaited()


class TestHandleErrors:
    async def test_passes_through_on_success(self):
        mock_fn = AsyncMock(return_value="success")

        decorated = handle_errors("test action")(mock_fn)
        result = await decorated()
        assert result == "success"

    async def test_re_raises_http_exception(self):
        mock_fn = AsyncMock(side_effect=HTTPException(status_code=400, detail="bad"))

        decorated = handle_errors()(mock_fn)
        with pytest.raises(HTTPException) as exc:
            await decorated()
        assert exc.value.status_code == 400

    async def test_wraps_generic_exception(self):
        mock_fn = AsyncMock(side_effect=ValueError("boom"))

        decorated = handle_errors("test")(mock_fn)
        with pytest.raises(HTTPException) as exc:
            await decorated()
        assert exc.value.status_code == 500
        assert "boom" in str(exc.value.detail)

    async def test_custom_action_name_in_log(self):
        mock_fn = AsyncMock(side_effect=RuntimeError("fail"))

        decorated = handle_errors("custom action")(mock_fn)
        with pytest.raises(HTTPException):
            await decorated()

    async def test_passes_args_to_wrapped(self):
        mock_fn = AsyncMock(return_value="done")

        decorated = handle_errors()(mock_fn)
        result = await decorated("arg1", key="val")
        assert result == "done"
        mock_fn.assert_awaited_once_with("arg1", key="val")
