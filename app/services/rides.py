"""Ride domain operations."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RideStatus, TripStatus
from app.models.ride import Ride
from app.models.rider import Rider
from app.models.trip import Trip

ACTIVE_RIDE_STATUSES = frozenset(
    {
        RideStatus.REQUESTED,
        RideStatus.MATCHING,
        RideStatus.DRIVER_ASSIGNED,
        RideStatus.DRIVER_ARRIVING,
        RideStatus.IN_PROGRESS,
    },
)


async def ensure_rider(session: AsyncSession, rider_id: uuid.UUID) -> Rider:
    rider = await session.get(Rider, rider_id)
    if rider is None:
        rider = Rider(id=rider_id)
        session.add(rider)
        await session.flush()
    return rider


async def create_ride(
    session: AsyncSession,
    *,
    rider_id: uuid.UUID,
    pickup: dict[str, Any],
    destination: dict[str, Any],
    tier,
    surge_zone_id: str | None,
    surge_multiplier: float | None,
    idempotency_key: str | None,
) -> tuple[Ride, Trip]:
    if idempotency_key:
        existing = await session.scalar(
            select(Ride).where(Ride.idempotency_key == idempotency_key),
        )
        if existing:
            trip = await session.scalar(select(Trip).where(Trip.ride_id == existing.id))
            if trip is None:
                msg = "Data inconsistency for idempotent ride"
                raise HTTPException(status_code=500, detail=msg)
            return existing, trip

    active_stmt = (
        select(Ride.id)
        .where(Ride.rider_id == rider_id, Ride.status.in_(ACTIVE_RIDE_STATUSES))
        .limit(1)
    )
    conflict = await session.scalar(active_stmt)
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rider already has an active ride",
        )

    await ensure_rider(session, rider_id)
    ride = Ride(
        rider_id=rider_id,
        status=RideStatus.MATCHING,
        pickup=pickup,
        destination=destination,
        tier=tier,
        surge_zone_id=surge_zone_id,
        surge_multiplier=surge_multiplier,
        idempotency_key=idempotency_key,
    )
    session.add(ride)
    await session.flush()
    trip = Trip(ride_id=ride.id, status=TripStatus.MATCHING)
    session.add(trip)
    await session.commit()
    await session.refresh(ride)
    await session.refresh(trip)
    from app.workers.tasks import match_ride

    match_ride.delay(str(ride.id))
    return ride, trip


async def get_ride_for_rider(
    session: AsyncSession,
    *,
    ride_id: uuid.UUID,
    rider_id: uuid.UUID,
) -> Ride:
    ride = await session.get(Ride, ride_id)
    if ride is None or ride.rider_id != rider_id:
        raise HTTPException(status_code=404, detail="Ride not found")
    return ride


async def cancel_ride(session: AsyncSession, ride: Ride, trip: Trip | None) -> None:
    if ride.status in (RideStatus.COMPLETED, RideStatus.CANCELLED):
        raise HTTPException(status_code=409, detail="Ride cannot be cancelled")
    ride.status = RideStatus.CANCELLED
    if trip and trip.status not in (TripStatus.COMPLETED, TripStatus.CANCELLED):
        trip.status = TripStatus.CANCELLED
    await session.commit()
