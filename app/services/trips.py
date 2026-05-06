"""Trip lifecycle updates."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.models.enums import DriverStatus, RideStatus, TripStatus
from app.models.ride import Ride
from app.models.trip import Trip
from app.notifications.dispatcher import notify_event
from app.pricing.service import compute_fare, estimate_duration_minutes, trip_distance_km
from app.pricing.surge import get_surge_multiplier
from app.services.trip_fsm import assert_transition
from app.utils.redis import get_redis
from app.websockets.manager import hub


async def _trip_for_uuid(session: AsyncSession, trip_id: uuid.UUID) -> tuple[Trip, Ride]:
    trip = await session.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    ride = await session.get(Ride, trip.ride_id)
    if ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")
    return trip, ride


def _align_ride_status(trip_status: TripStatus) -> RideStatus | None:
    mapping = {
        TripStatus.DRIVER_ASSIGNED: RideStatus.DRIVER_ASSIGNED,
        TripStatus.DRIVER_ARRIVING: RideStatus.DRIVER_ARRIVING,
        TripStatus.IN_PROGRESS: RideStatus.IN_PROGRESS,
        TripStatus.PAUSED: RideStatus.IN_PROGRESS,
        TripStatus.COMPLETED: RideStatus.COMPLETED,
        TripStatus.CANCELLED: RideStatus.CANCELLED,
    }
    return mapping.get(trip_status)


async def start_trip(session: AsyncSession, trip_id: uuid.UUID) -> Trip:
    trip, ride = await _trip_for_uuid(session, trip_id)
    assert_transition(trip.status, TripStatus.IN_PROGRESS)
    trip.status = TripStatus.IN_PROGRESS
    trip.started_at = datetime.now(UTC)
    rs = _align_ride_status(trip.status)
    if rs:
        ride.status = rs
    await session.commit()
    await session.refresh(trip)
    notify_event(event_type="trip_started", payload={"trip_id": str(trip.id)})
    await hub.broadcast(
        hub.ride_channel(ride.id),
        {"type": "trip_started", "trip_id": str(trip.id)},
    )
    return trip


async def pause_trip(session: AsyncSession, trip_id: uuid.UUID) -> Trip:
    trip, ride = await _trip_for_uuid(session, trip_id)
    assert_transition(trip.status, TripStatus.PAUSED)
    trip.status = TripStatus.PAUSED
    trip.paused_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(trip)
    return trip


async def resume_trip(session: AsyncSession, trip_id: uuid.UUID) -> Trip:
    trip, ride = await _trip_for_uuid(session, trip_id)
    assert_transition(trip.status, TripStatus.IN_PROGRESS)
    trip.status = TripStatus.IN_PROGRESS
    trip.paused_at = None
    rs = _align_ride_status(trip.status)
    if rs:
        ride.status = rs
    await session.commit()
    await session.refresh(trip)
    return trip


async def end_trip(session: AsyncSession, trip_id: uuid.UUID) -> Trip:
    redis = get_redis()
    trip, ride = await _trip_for_uuid(session, trip_id)
    assert_transition(trip.status, TripStatus.COMPLETED)
    dist = trip_distance_km(ride.pickup, ride.destination)
    dur = estimate_duration_minutes(dist)
    zone = ride.surge_zone_id
    surge = await get_surge_multiplier(redis, zone, default=ride.surge_multiplier or 1.0)
    fare = compute_fare(
        distance_km=dist,
        duration_minutes=dur,
        surge_multiplier=float(surge),
    )
    trip.fare = fare
    trip.status = TripStatus.COMPLETED
    trip.ended_at = datetime.now(UTC)
    ride.status = RideStatus.COMPLETED
    if ride.driver_id:
        driver = await session.get(Driver, ride.driver_id)
        if driver is not None:
            driver.status = DriverStatus.ONLINE
    await session.commit()
    await session.refresh(trip)
    notify_event(event_type="trip_completed", payload={"trip_id": str(trip.id), "fare": str(fare)})
    await hub.broadcast(
        hub.ride_channel(ride.id),
        {"type": "trip_completed", "trip_id": str(trip.id), "fare": fare},
    )
    from app.workers.tasks import analytics_stub

    analytics_stub.delay("trip_completed")
    return trip
