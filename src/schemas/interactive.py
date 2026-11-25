"""Pydantic request schemas for interactive and native-flow messages."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class BaseWhatsAppRequest(BaseModel):
    phone: str
    type: Optional[str] = None
    quoted_id: Optional[str] = None
    delay_message: Optional[Union[int, float, str]] = None
    delay_typing: Optional[Union[int, float]] = None
    mentioned: Optional[List[str]] = None


try:
    from src.schemas.send import BaseWhatsAppRequest as _BaseWhatsAppRequest

    BaseWhatsAppRequest = _BaseWhatsAppRequest  # type: ignore[misc]
except Exception:
    pass


class NativeFlowButton(BaseModel):
    """A single native-flow button (name + params serialized once)."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: str
    params: Optional[Any] = Field(default=None, alias="params")
    button_params_json: Optional[str] = Field(default=None, alias="buttonParamsJSON")
    buttonParamsJSON: Optional[str] = Field(default=None, exclude=True)

    def serialized_params(self) -> str:
        if self.button_params_json is not None:
            return self.button_params_json
        if self.buttonParamsJSON is not None:
            return self.buttonParamsJSON
        value = self.params
        if value is None:
            return "{}"
        if isinstance(value, str):
            try:
                json.loads(value)
                return value
            except (ValueError, TypeError):
                return json.dumps({"value": value}, ensure_ascii=False)
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class SendNativeFlowRequest(BaseWhatsAppRequest):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    body: Optional[str] = Field(default=None, alias="body")
    message: Optional[str] = Field(default=None, alias="message")
    text: Optional[str] = Field(default=None, alias="text")
    title: Optional[str] = None
    footer: Optional[str] = None
    image: Optional[str] = None
    version: int = Field(default=1, alias="version")
    message_params: Optional[Any] = Field(default=None, alias="messageParams")
    message_params_json: Optional[str] = Field(default=None, alias="messageParamsJSON")
    buttons: Optional[List[NativeFlowButton]] = Field(default=None, alias="buttons")
    actions: Optional[List[NativeFlowButton]] = Field(default=None, alias="actions")

    def resolved_buttons(self) -> List[NativeFlowButton]:
        if self.buttons:
            return list(self.buttons)
        if self.actions:
            return list(self.actions)
        return []

    def resolved_text(self) -> str:
        return self.body or self.text or self.message or ""

    def serialized_message_params(self) -> Optional[str]:
        if self.message_params_json is not None:
            return self.message_params_json
        value = self.message_params
        if value is None:
            return None
        if isinstance(value, str):
            try:
                json.loads(value)
                return value
            except (ValueError, TypeError):
                return json.dumps({"value": value}, ensure_ascii=False)
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class QuickReplyAction(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    type: Literal["reply", "quick_reply"] = "reply"
    id: Optional[str] = None
    text: Optional[str] = None
    display_text: Optional[str] = None


class UrlAction(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    type: Literal["url", "cta_url"] = "url"
    url: str
    text: Optional[str] = None
    display_text: Optional[str] = None
    webview_interaction: bool = False


class CopyAction(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    type: Literal["copy", "cta_copy"] = "copy"
    copy_code: Optional[str] = None
    code: Optional[str] = None
    text: Optional[str] = None
    display_text: Optional[str] = None


class CallAction(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    type: Literal["call", "cta_call"] = "call"
    phone_number: Optional[str] = Field(default=None, alias="phoneNumber")
    id: Optional[str] = None
    text: Optional[str] = None
    display_text: Optional[str] = None


class ReminderAction(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    type: Literal["reminder", "cta_reminder"] = "reminder"
    id: Optional[str] = None
    text: Optional[str] = None
    display_text: Optional[str] = None


class CancelReminderAction(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    type: Literal["cancel_reminder", "cta_cancel_reminder"] = "cancel_reminder"
    id: Optional[str] = None
    text: Optional[str] = None
    display_text: Optional[str] = None


class AddressAction(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    type: Literal["address", "address_message"] = "address"
    id: Optional[str] = None
    text: Optional[str] = None
    display_text: Optional[str] = None


class LocationRequestAction(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    type: Literal["location", "send_location", "location_request"] = "location"
    extra: Optional[Dict[str, Any]] = None


class SelectionAction(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    type: Literal["selection", "single_select"] = "selection"
    title: Optional[str] = None
    sections: Optional[List[Dict[str, Any]]] = None
    text: Optional[str] = None
    display_text: Optional[str] = None


InteractiveAction = Union[
    QuickReplyAction,
    UrlAction,
    CopyAction,
    CallAction,
    ReminderAction,
    CancelReminderAction,
    AddressAction,
    LocationRequestAction,
    SelectionAction,
]


class SendInteractiveRequest(BaseWhatsAppRequest):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    header: Optional[Dict[str, Any]] = None
    body: Optional[str] = None
    text: Optional[str] = None
    message: Optional[str] = None
    footer: Optional[str] = None
    actions: Optional[List[InteractiveAction]] = None
    buttons: Optional[List[InteractiveAction]] = None


class CarouselCard(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    header: Optional[Dict[str, Any]] = None
    body: Optional[str] = None
    footer: Optional[str] = None
    actions: Optional[List[InteractiveAction]] = None


class SendCarouselRequest(BaseWhatsAppRequest):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    cards: Optional[List[CarouselCard]] = None
    body: Optional[str] = None
    footer: Optional[str] = None