"""Tests for orders repository (Fase 3)."""

import pytest

from src.repositories import orders as repo


def test_persist_idempotent_and_session_isolation(temp_db):
    repo.persist_order_header("1", "O1", title="Order", total_1000=1000, currency="BRL")
    repo.persist_order_header("1", "O1", title="Order", total_1000=1000, currency="BRL")
    repo.persist_order_header("2", "O1", title="Other", total_1000=2000, currency="USD")

    o1 = repo.get_order("1", "O1")
    o2 = repo.get_order("2", "O1")
    assert o1 is not None
    assert o2 is not None
    assert o1["title"] == "Order"
    assert o2["title"] == "Other"
    assert "token" not in o1

    listed = repo.list_orders("1")
    assert listed["total"] == 1

    repo.replace_order_items("1", "O1", [{"name": "Item", "quantity": 2, "price_1000": 500, "currency": "BRL"}])
    o1 = repo.get_order("1", "O1")
    assert len(o1["items"]) == 1
    assert o1["items"][0]["name"] == "Item"

    repo.add_event("1", "O1", "order.updated", metadata={"x": 1})
    o1 = repo.get_order("1", "O1")
    assert len(o1["events"]) == 1