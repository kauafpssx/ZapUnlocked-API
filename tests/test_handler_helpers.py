"""Tests for handler helper utilities."""

from unittest.mock import MagicMock

import pytest

from src.handlers.helpers import _has, _safe_str, _safe_int, _detect_type


class ObjWithAttr:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestHas:
    def test_returns_true_when_field_set(self):
        obj = ObjWithAttr(name="John")
        assert _has(obj, "name") is True

    def test_returns_false_when_field_none(self):
        obj = ObjWithAttr(value=None)
        assert _has(obj, "value") is False

    def test_returns_false_when_field_default(self):
        obj = ObjWithAttr(count=0)
        assert _has(obj, "count") is False

    def test_returns_false_when_field_missing(self):
        obj = ObjWithAttr()
        assert _has(obj, "nonexistent") is False


class TestSafeStr:
    def test_returns_string_value(self):
        obj = ObjWithAttr(name="hello")
        assert _safe_str(obj, "name") == "hello"

    def test_returns_empty_for_none(self):
        obj = ObjWithAttr(name=None)
        assert _safe_str(obj, "name") == ""

    def test_returns_empty_for_attribute_error(self):
        obj = ObjWithAttr()
        assert _safe_str(obj, "nonexistent") == ""


class TestSafeInt:
    def test_returns_int_value(self):
        obj = ObjWithAttr(count=42)
        assert _safe_int(obj, "count") == 42

    def test_returns_zero_for_none(self):
        obj = ObjWithAttr(value=None)
        assert _safe_int(obj, "value") == 0

    def test_returns_zero_for_attribute_error(self):
        obj = ObjWithAttr()
        assert _safe_int(obj, "nonexistent") == 0


class TestDetectType:
    def test_detects_conversation(self):
        raw = MagicMock()
        raw.conversation = "hello"
        assert _detect_type(raw) == "conversation"

    def test_detects_image_message(self):
        raw = MagicMock(spec=[])
        raw.conversation = None
        raw.extendedTextMessage = None
        raw.imageMessage = "data"
        assert _detect_type(raw) == "imageMessage"

    def test_detects_extended_text(self):
        raw = MagicMock(spec=[])
        raw.conversation = None
        raw.extendedTextMessage = "data"
        assert _detect_type(raw) == "extendedTextMessage"

    def test_returns_unknown_when_none_set(self):
        raw = MagicMock(spec=[])
        raw.conversation = None
        raw.extendedTextMessage = None
        assert _detect_type(raw) == "unknown"
