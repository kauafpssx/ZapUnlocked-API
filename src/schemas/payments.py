"""Payment schemas (Fase 4)."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


PixKeyType = Literal["EVP", "CPF", "CNPJ", "PHONE", "EMAIL"]


class PaymentBaseRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    phone: Optional[str] = None
    order_id: Optional[str] = Field(default=None, alias="orderId")
    reference_id: Optional[str] = Field(default=None, alias="referenceId")
    amount_1000: int = Field(..., alias="amount1000")
    currency: str = "BRL"
    offset: int = 100
    pix_key: str = Field(..., alias="pixKey")
    pix_key_type: PixKeyType = Field(default="EVP", alias="pixKeyType")
    merchant_name: str = Field(..., alias="merchantName")
    city: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None
    title: Optional[str] = None
    footer: Optional[str] = None


class PaymentInfoRequest(PaymentBaseRequest):
    pass


class ReviewAndPayRequest(PaymentBaseRequest):
    pass