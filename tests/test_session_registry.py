"""Tests for src/services/sessions/registry.py — SQLite session CRUD."""

import pytest

from src.services.sessions.registry import (
    create_session,
    delete_session,
    ensure_default_session,
    get_active_sessions,
    get_default_session_id,
    get_session,
    list_sessions,
    rename_session,
)


class TestEnsureDefaultSession:
    def test_creates_session_1(self, temp_db):
        ensure_default_session()
        sessions = list_sessions()
        assert any(s["id"] == "1" for s in sessions)

    def test_idempotent(self, temp_db):
        ensure_default_session()
        ensure_default_session()
        sessions = list_sessions()
        assert len([s for s in sessions if s["id"] == "1"]) == 1

    def test_default_name_is_default(self, temp_db):
        ensure_default_session()
        s = get_session("1")
        assert s["name"] == "Default"

    def test_default_session_is_active(self, temp_db):
        ensure_default_session()
        s = get_session("1")
        assert s["active"] is True


class TestListSessions:
    def test_empty_initially(self, temp_db):
        assert list_sessions() == []

    def test_returns_all_sessions(self, temp_db):
        ensure_default_session()
        create_session("second")
        sessions = list_sessions()
        assert len(sessions) == 2

    def test_ordered_by_id(self, temp_db):
        ensure_default_session()
        create_session("extra")
        ids = [s["id"] for s in list_sessions()]
        assert ids == sorted(ids)


class TestGetSession:
    def test_returns_none_for_missing(self, temp_db):
        assert get_session("999") is None

    def test_returns_session(self, temp_db):
        ensure_default_session()
        s = get_session("1")
        assert s is not None
        assert s["id"] == "1"

    def test_active_field_is_bool(self, temp_db):
        ensure_default_session()
        s = get_session("1")
        assert isinstance(s["active"], bool)


class TestCreateSession:
    def test_creates_with_custom_name(self, temp_db):
        s = create_session("MySession")
        assert s["name"] == "MySession"
        assert s["active"] is True

    def test_auto_name_equals_id_when_none(self, temp_db):
        s = create_session()
        assert s["name"] == s["id"]

    def test_auto_increments_id(self, temp_db):
        ensure_default_session()
        s2 = create_session("second")
        assert s2["id"] == "2"

    def test_fills_gaps_in_ids(self, temp_db):
        ensure_default_session()
        s2 = create_session("two")
        delete_session("1")
        s_new = create_session("new")
        assert s_new["id"] == "1"

    def test_persists_to_db(self, temp_db):
        create_session("persisted")
        sessions = list_sessions()
        assert any(s["name"] == "persisted" for s in sessions)


class TestRenameSession:
    def test_renames_existing(self, temp_db):
        ensure_default_session()
        s = rename_session("1", "Renamed")
        assert s["name"] == "Renamed"

    def test_raises_for_missing(self, temp_db):
        with pytest.raises(ValueError, match="not found"):
            rename_session("999", "Ghost")


class TestDeleteSession:
    def test_deletes_existing(self, temp_db):
        ensure_default_session()
        delete_session("1")
        assert get_session("1") is None

    def test_raises_for_missing(self, temp_db):
        with pytest.raises(ValueError, match="not found"):
            delete_session("999")


class TestGetDefaultSessionId:
    def test_returns_1_when_no_sessions(self, temp_db):
        assert get_default_session_id() == "1"

    def test_returns_first_active(self, temp_db):
        ensure_default_session()
        create_session("second")
        assert get_default_session_id() == "1"

    def test_returns_next_when_1_deleted(self, temp_db):
        ensure_default_session()
        create_session("second")
        delete_session("1")
        assert get_default_session_id() == "2"


class TestGetActiveSessions:
    def test_empty_when_no_sessions(self, temp_db):
        assert get_active_sessions() == []

    def test_returns_active_sessions(self, temp_db):
        ensure_default_session()
        create_session("two")
        active = get_active_sessions()
        assert len(active) == 2
        assert all(s["active"] for s in active)
