"""Pydantic request schemas for contact management."""

from pydantic import BaseModel


class BlockRequest(BaseModel):
    phone: str
    action: str  # "block" | "unblock"
