"""Tests for orders service (Fase 3)."""

import pytest

from src.repositories import orders as repo
from src.services.whatsapp import orders as order_service


def test_list_filters_and_pagination(temp_db):
    repo.persist_order_header("1", "O1", currency="BRL", total_1000=1000, local_status="received")
    repo.persist_order_header("1", "O2", currency="USD", total_1000=2000, local_status="accepted")
    repo.persist_order_header("2", "O3", currency="BRL", total_1000=3000)

    page = order_service.list_orders("1", currency="BRL", limit=10, offset=0)
    assert page["total"] == 1
    assert page["orders"][0]["order_id"] == "O1"

    all_orders = order_service.list_orders("1", limit=1, offset=0)
    assert all_orders["total"] == 2
    assert len(all_orders["orders"]) == 1


def test_update_order_creates_audit_event(temp_db):
    repo.persist_order_header("1", "O1", local_status="received")
    updated = __import__("asyncio").run(order_service.update_order("1", "O1", {"local_status": "accepted", "note": "ok"}))
    assert updated is not None
    assert updated["local_status"] == "accepted"
    assert updated["note"] == "ok"
    events = repo.get_order("1", "O1")["events"]
    assert any(e["event_type"] == "order.local_status_changed" for e in events)


def test_refresh_without_token_fails(temp_db):
    repo.persist_order_header("1", "O1")
    result = __import__("asyncio").run(order_service.refresh_order("1", "O1"))
    assert result["success"] is False
    assert result["error"] == "TOKEN_UNAVAILABLE"


def test_get_order_missing_returns_none(temp_db):
    assert order_service.get_order("1", "NOPE") is None