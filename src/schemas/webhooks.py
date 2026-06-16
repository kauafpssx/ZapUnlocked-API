"""Pydantic request schemas for webhook management."""

from pydantic import BaseModel
from typing import Optional


class WebhookCreateRequest(BaseModel):
    name: str
    url: str
    method: str = "POST"
    headers: dict = {}
    body: dict = {}
    events: list[str] = ["*"]
    active: bool = True
    secret: Optional[str] = None


class WebhookUpdateRequest(BaseModel):
    url: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[dict] = None
    body: Optional[dict] = None
    events: Optional[list[str]] = None
    active: Optional[bool] = None
    secret: Optional[str] = None


class WebhookToggleRequest(BaseModel):
    active: Optional[bool] = None
