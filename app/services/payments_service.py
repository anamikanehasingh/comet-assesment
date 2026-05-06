"""Mock payment service + idempotency."""

from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PaymentStatus, TripStatus
from app.models.payment import Payment
from app.models.ride import Ride
from app.models.trip import Trip
from app.notifications.dispatcher import notify_event
from app.websockets.manager import hub


async def initiate_payment(
    session: AsyncSession,
    *,
    trip_id: uuid.UUID,
    amount: float,
    currency: str,
    idempotency_key: str | None,
) -> Payment:
    if idempotency_key:
        existing = await session.scalar(
            select(Payment).where(Payment.idempotency_key == idempotency_key),
        )
        if existing:
            return existing

    trip = await session.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.status != TripStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Trip must be completed before payment")

    pay = Payment(
        trip_id=trip_id,
        amount=amount,
        currency=currency,
        status=PaymentStatus.PROCESSING,
        idempotency_key=idempotency_key,
        provider_ref=None,
    )
    session.add(pay)
    await session.flush()

    if round(amount * 100) % 100 == 99:
        pay.status = PaymentStatus.FAILED
        pay.meta = {"reason": "mock_psp_decline"}
        await session.commit()
        notify_event(event_type="payment_failed", payload={"payment_id": str(pay.id)})
        await session.refresh(pay)
        from app.workers.tasks import retry_payment

        retry_payment.apply_async(args=[str(pay.id)], countdown=30)
        ride = await session.get(Ride, trip.ride_id)
        if ride:
            await hub.broadcast(
                hub.ride_channel(ride.id),
                {"type": "payment_failed", "payment_id": str(pay.id)},
            )
        return pay

    pay.status = PaymentStatus.SUCCEEDED
    pay.provider_ref = f"mock_psp_{pay.id}"
    await session.commit()
    await session.refresh(pay)
    notify_event(event_type="payment_succeeded", payload={"payment_id": str(pay.id)})
    ride = await session.get(Ride, trip.ride_id)
    if ride:
        await hub.broadcast(
            hub.ride_channel(ride.id),
            {"type": "payment_succeeded", "payment_id": str(pay.id)},
        )
    return pay
