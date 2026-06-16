"""Tests for src/utils/phone.py — resolve_jid()."""

import pytest

from src.utils.phone import resolve_jid


class TestResolveJid:
    def test_bare_number_appends_suffix(self):
        assert resolve_jid("5511999999999") == "5511999999999@s.whatsapp.net"

    def test_already_individual_jid_unchanged(self):
        jid = "5511999999999@s.whatsapp.net"
        assert resolve_jid(jid) == jid

    def test_group_jid_unchanged(self):
        jid = "120363000000000001@g.us"
        assert resolve_jid(jid) == jid

    def test_strips_plus_prefix(self):
        assert resolve_jid("+5511999999999") == "5511999999999@s.whatsapp.net"

    def test_strips_spaces(self):
        assert resolve_jid("55 11 99999 9999") == "5511999999999@s.whatsapp.net"

    def test_strips_plus_and_spaces(self):
        assert resolve_jid("+55 11 99999-9999".replace("-", "")) == "5511999999999@s.whatsapp.net"

    def test_empty_string_still_appends_suffix(self):
        assert resolve_jid("") == "@s.whatsapp.net"

    def test_number_with_country_code(self):
        assert resolve_jid("12025550100") == "12025550100@s.whatsapp.net"
