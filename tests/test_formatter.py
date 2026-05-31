"""Tests for the text formatter with date/time placeholders."""

import re

import pytest

from src.utils.formatter import format_text


class TestFormatText:
    def test_plain_text_passes_through(self):
        result = format_text("Hello world")
        assert result == "Hello world"

    def test_none_returns_none(self):
        result = format_text(None)
        assert result is None

    def test_empty_string_returns_empty(self):
        result = format_text("")
        assert result == ""

    def test_non_string_returns_as_is(self):
        result = format_text(123)
        assert result == 123

    def test_replaces_day_placeholder(self):
        result = format_text("{{day}}")
        assert re.match(r"^\d{2}$", result)

    def test_replaces_mon_placeholder(self):
        result = format_text("{{mon}}")
        assert re.match(r"^\d{2}$", result)

    def test_replaces_yea_placeholder(self):
        result = format_text("{{yea}}")
        assert re.match(r"^\d{4}$", result)

    def test_replaces_hou_placeholder(self):
        result = format_text("{{hou}}")
        assert re.match(r"^\d{2}$", result)

    def test_replaces_min_placeholder(self):
        result = format_text("{{min}}")
        assert re.match(r"^\d{2}$", result)

    def test_replaces_sec_placeholder(self):
        result = format_text("{{sec}}")
        assert re.match(r"^\d{2}$", result)

    def test_replaces_all_placeholders(self):
        result = format_text("{{day}}/{{mon}}/{{yea}} {{hou}}:{{min}}:{{sec}}")
        assert re.match(r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$", result)

    def test_unknown_placeholder_left_untouched(self):
        result = format_text("{{foo}}")
        assert result == "{{foo}}"

    def test_mixed_known_and_unknown(self):
        result = format_text("{{day}}-{{foo}}")
        assert "{{foo}}" in result
        assert re.match(r"^\d{2}", result)

    def test_placeholder_in_middle_of_text(self):
        result = format_text("Today is {{day}}/{{mon}}/{{yea}}")
        assert "Today is " in result
