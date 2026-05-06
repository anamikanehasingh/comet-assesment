"""Payments."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    trip_id: str
    amount: float = Field(..., gt=0)
    currency: str = "USD"


class PaymentResponse(BaseModel):
    payment_id: str
    trip_id: str
    status: str
    amount: float
    provider_ref: str | None = None
