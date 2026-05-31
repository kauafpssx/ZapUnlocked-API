"""Tests for the IP rules service (blacklist/whitelist)."""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.services.ip_rules_service import (
    get_ip_rules,
    add_ip,
    remove_ip,
    is_ip_blocked,
    is_ip_allowed,
)


@pytest.fixture(autouse=True)
def temp_rules_file(tmp_path: Path):
    """Redirect RULES_FILE to a temp path and seed with defaults."""
    dummy_file = tmp_path / "ip_rules.json"
    dummy_file.parent.mkdir(parents=True, exist_ok=True)
    dummy_file.write_text('{"whitelist": [], "blacklist": []}')
    with patch("src.services.ip_rules_service.RULES_FILE", dummy_file):
        yield


class TestGetIpRules:
    def test_returns_default_structure(self):
        rules = get_ip_rules()
        assert "whitelist" in rules
        assert "blacklist" in rules
        assert rules["whitelist"] == []
        assert rules["blacklist"] == []

    def test_returns_existing_rules(self):
        add_ip("whitelist", "192.168.1.1")
        rules = get_ip_rules()
        assert "192.168.1.1" in rules["whitelist"]


class TestAddIp:
    def test_add_to_whitelist(self):
        result = add_ip("whitelist", "10.0.0.1")
        assert "10.0.0.1" in result["whitelist"]

    def test_add_to_blacklist(self):
        result = add_ip("blacklist", "10.0.0.1")
        assert "10.0.0.1" in result["blacklist"]

    def test_add_duplicate_is_idempotent(self):
        add_ip("whitelist", "10.0.0.1")
        result = add_ip("whitelist", "10.0.0.1")
        assert result["whitelist"] == ["10.0.0.1"]

    def test_add_invalid_list_raises(self):
        with pytest.raises(ValueError, match="Invalid list name"):
            add_ip("invalid_list", "10.0.0.1")


class TestRemoveIp:
    def test_remove_from_whitelist(self):
        add_ip("whitelist", "10.0.0.1")
        result = remove_ip("whitelist", "10.0.0.1")
        assert "10.0.0.1" not in result["whitelist"]

    def test_remove_nonexistent_is_safe(self):
        result = remove_ip("whitelist", "10.0.0.1")
        assert result["whitelist"] == []

    def test_remove_invalid_list_raises(self):
        with pytest.raises(ValueError, match="Invalid list name"):
            remove_ip("invalid_list", "10.0.0.1")


class TestIsIpBlocked:
    def test_ip_in_blacklist_returns_true(self):
        add_ip("blacklist", "10.0.0.99")
        assert is_ip_blocked("10.0.0.99") is True

    def test_ip_not_in_blacklist_returns_false(self):
        assert is_ip_blocked("10.0.0.99") is False

    def test_ip_in_whitelist_not_blocked(self):
        add_ip("whitelist", "10.0.0.1")
        assert is_ip_blocked("10.0.0.1") is False


class TestIsIpAllowed:
    def test_empty_whitelist_allows_all(self):
        assert is_ip_allowed("10.0.0.1") is True

    def test_ip_in_whitelist_allowed(self):
        add_ip("whitelist", "10.0.0.1")
        assert is_ip_allowed("10.0.0.1") is True

    def test_ip_not_in_whitelist_denied(self):
        add_ip("whitelist", "10.0.0.1")
        assert is_ip_allowed("10.0.0.2") is False

    def test_blacklisted_ip_returns_none(self):
        add_ip("blacklist", "10.0.0.99")
        assert is_ip_allowed("10.0.0.99") is None

    def test_blacklist_takes_priority_over_whitelist(self):
        add_ip("whitelist", "10.0.0.1")
        add_ip("blacklist", "10.0.0.1")
        assert is_ip_allowed("10.0.0.1") is None
