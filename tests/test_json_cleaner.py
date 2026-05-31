"""Tests for the JSON comment stripper utility."""

import pytest

from src.utils.parsing.json_cleaner import clean_json_text


class TestCleanJsonText:
    def test_clean_json_passes_through(self):
        result = clean_json_text('{"key": "value"}')
        assert result == '{"key": "value"}'

    def test_removes_single_line_comment(self):
        result = clean_json_text('{"key": "value"} // comment')
        assert result == '{"key": "value"}'

    def test_removes_inline_comment(self):
        result = clean_json_text('{"key": "value" /* block */}')
        assert result == '{"key": "value" }'

    def test_removes_multi_line_comment(self):
        text = '{"key": /* multi\\nline */ "value"}'
        result = clean_json_text(text)
        assert result == '{"key":  "value"}'

    def test_removes_trailing_comma_in_object(self):
        result = clean_json_text('{"a": 1, "b": 2,}')
        assert result == '{"a": 1, "b": 2}'

    def test_removes_trailing_comma_in_array(self):
        result = clean_json_text('[1, 2, 3,]')
        assert result == '[1, 2, 3]'

    def test_preserves_url_with_colon(self):
        text = '{"url": "https://example.com"}'
        result = clean_json_text(text)
        assert result == text

    def test_comment_after_url_preserved(self):
        text = '{"url": "https://example.com/path"} // ok'
        result = clean_json_text(text)
        assert '// ok' not in result
        assert "https://example.com/path" in result

    def test_empty_string_returns_empty(self):
        result = clean_json_text("")
        assert result == ""

    def test_only_comment_returns_empty(self):
        result = clean_json_text("// just a comment")
        assert result == ""

    def test_nested_structures(self):
        text = '{"data": [1, 2, /* mid */ 3,],}'
        result = clean_json_text(text)
        assert result == '{"data": [1, 2,  3]}'

    def test_trailing_newlines_stripped(self):
        result = clean_json_text('{"a": 1}\n\n  ')
        assert result == '{"a": 1}'
