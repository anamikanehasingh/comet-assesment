"""Payments (mock PSP)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request

from app.api.deps import DbSession
from app.core.security import require_auth
from app.schemas.payments import PaymentCreate, PaymentResponse
from app.services.payments_service import initiate_payment

router = APIRouter(dependencies=[Depends(require_auth)])


@router.post("/payments", response_model=PaymentResponse)
async def post_payment(
    request: Request,
    body: PaymentCreate,
    session: DbSession,
) -> PaymentResponse:
    idem = getattr(request.state, "idempotency_key", None)
    pay = await initiate_payment(
        session,
        trip_id=uuid.UUID(body.trip_id),
        amount=body.amount,
        currency=body.currency,
        idempotency_key=idem,
    )
    return PaymentResponse(
        payment_id=str(pay.id),
        trip_id=str(pay.trip_id),
        status=pay.status.value,
        amount=float(pay.amount),
        provider_ref=pay.provider_ref,
    )


@router.post("/payments/webhook")
async def payments_webhook(payload: dict) -> dict:
    """Stub PSP webhook — accepts body and returns ack (no signature verification in MVP)."""

    return {"received": True, "echo": payload}
