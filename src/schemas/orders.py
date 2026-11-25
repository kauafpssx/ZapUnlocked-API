"""Pydantic request schemas for orders."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OrderListQuery(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    session_id: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    local_status: Optional[str] = Field(default=None, alias="localStatus")
    currency: Optional[str] = None
    date_from: Optional[str] = Field(default=None, alias="dateFrom")
    date_to: Optional[str] = Field(default=None, alias="dateTo")
    limit: int = 50
    offset: int = 0


class OrderPatchRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    local_status: Optional[str] = Field(default=None, alias="localStatus")
    note: Optional[str] = None
    title: Optional[str] = None
    # Local adjustments (stored in audit trail).
    quantity: Optional[int] = None
    price: Optional[int] = None
    discount: Optional[int] = None
    shipping: Optional[int] = None
    adjustments: Optional[dict[str, Any]] = None


class OrderCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    order_id: Optional[str] = Field(default=None, alias="orderId")
    title: Optional[str] = None
    currency: Optional[str] = "BRL"
    total_1000: Optional[int] = Field(default=None, alias="totalAmount1000")
    local_status: Optional[str] = Field(default="received", alias="localStatus")
    note: Optional[str] = None
    chat_jid: Optional[str] = Field(default=None, alias="chatJid")
    seller_jid: Optional[str] = Field(default=None, alias="sellerJid")
    items: Optional[List[dict[str, Any]]] = None