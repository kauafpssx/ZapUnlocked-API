"""Pydantic request schemas for settings and instance management."""

from pydantic import BaseModel
from typing import Optional


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    newProfilePictureUrl: Optional[str] = None


class PrivacyUpdateRequest(BaseModel):
    lastSeen: Optional[str] = None          # all | contacts | none | match_last_seen
    online: Optional[str] = None            # all | contacts | none | match_last_seen
    profile: Optional[str] = None           # all | contacts | none
    status: Optional[str] = None            # all | contacts | none
    readReceipts: Optional[str] = None      # all | contacts | none
    groupsAdd: Optional[str] = None         # all | contacts | none
    callAdd: Optional[str] = None           # all | contacts | none
    about: Optional[str] = None             # status message / bio
    disappearingTimer: Optional[int] = None # hours (0 = off, 24 = 1 day, 168 = 7 days)


class UpdateInstanceNameRequest(BaseModel):
    name: str


class CallRejectRequest(BaseModel):
    value: bool


class CallRejectMessageRequest(BaseModel):
    value: str


class AutoReadRequest(BaseModel):
    value: bool
