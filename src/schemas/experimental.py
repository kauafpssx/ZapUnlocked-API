"""Experimental native form (galaxy_message) support.

Guarded by ENABLE_EXPERIMENTAL_NATIVE_FORMS=true. Payloads and rendering are
not guaranteed across WhatsApp clients; treat as unstable.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

try:
    from src.schemas.send import BaseWhatsAppRequest as _Base
except Exception:  # pragma: no cover
    from pydantic import BaseModel as _Base


class SendFormRequest(_Base):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    body: Optional[str] = Field(default=None, alias="body")
    message: Optional[str] = Field(default=None, alias="message")
    text: Optional[str] = Field(default=None, alias="text")
    title: Optional[str] = None
    footer: Optional[str] = None
    image: Optional[str] = None
    version: int = Field(default=3, alias="version")
    # Form payload (serialized once by the service).
    params: Optional[Any] = Field(default=None, alias="params")
    message_params: Optional[Any] = Field(default=None, alias="messageParams")
    fallback_url: Optional[str] = Field(default=None, alias="fallbackUrl")
    components: Optional[Any] = Field(default=None, alias="components")
    flow_id: Optional[str] = Field(default=None, alias="flowId")
    flow_token: Optional[str] = Field(default=None, alias="flowToken")
    flow_cta: Optional[str] = Field(default=None, alias="flowCta")
    full_name_visible: bool = Field(default=True, alias="fullNameVisible")
    email_visible: bool = Field(default=True, alias="emailVisible")
    phone_number_visible: bool = Field(default=False, alias="phoneNumberVisible")
    delivery_address_visible: bool = Field(default=False, alias="deliveryAddressVisible")
    custom_fields: Optional[Any] = Field(default=None, alias="customFields")


def is_enabled() -> bool:
    return os.getenv("ENABLE_EXPERIMENTAL_NATIVE_FORMS", "false").lower() in ("1", "true", "yes")