"""Driver-facing operations (location, matching responses)."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.matching.geo_service import geoadd_driver, georem_driver
from app.matching.offers import clear_offer_async, get_offer_for_driver_async
from app.models.driver import Driver
from app.models.enums import DriverStatus, RideStatus, TripStatus
from app.models.ride import Ride
from app.models.trip import Trip
from app.notifications.dispatcher import notify_event
from app.utils.redis import get_redis
from app.websockets.manager import hub


async def ensure_driver(session: AsyncSession, driver_id: uuid.UUID) -> Driver:
    d = await session.get(Driver, driver_id)
    if d is None:
        d = Driver(id=driver_id, status=DriverStatus.OFFLINE)
        session.add(d)
        await session.flush()
    return d


async def update_location(
    session: AsyncSession,
    *,
    driver_id: uuid.UUID,
    lat: float,
    lng: float,
) -> None:
    settings = get_settings()
    redis = get_redis()
    d = await ensure_driver(session, driver_id)
    if d.status == DriverStatus.ONLINE:
        await geoadd_driver(redis, driver_id, lng, lat)

    throttle_key = f"comet:driver_db_loc:{driver_id}"
    if await redis.set(throttle_key, "1", nx=True, ex=settings.DRIVER_LOCATION_DB_THROTTLE_SECONDS):
        d.last_lat = lat
        d.last_lng = lng
        await session.commit()
    else:
        await session.rollback()


async def set_availability(
    session: AsyncSession,
    *,
    driver_id: uuid.UUID,
    status_value: DriverStatus,
) -> Driver:
    redis = get_redis()
    d = await ensure_driver(session, driver_id)
    if status_value == DriverStatus.OFFLINE:
        await georem_driver(redis, driver_id)
    d.status = status_value
    await session.commit()
    await session.refresh(d)
    return d


async def accept_offer(
    session: AsyncSession,
    *,
    driver_id: uuid.UUID,
    ride_id: uuid.UUID,
    token: str,
) -> tuple[Ride, Trip]:
    redis = get_redis()
    offer = await get_offer_for_driver_async(redis, driver_id)
    if offer is None or offer.ride_id != ride_id or offer.token != token:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid or expired offer")

    async with session.begin():
        ride = (
            await session.scalars(select(Ride).where(Ride.id == ride_id).with_for_update())
        ).one_or_none()
        driver = (
            await session.scalars(select(Driver).where(Driver.id == driver_id).with_for_update())
        ).one_or_none()
        trip = (await session.scalars(select(Trip).where(Trip.ride_id == ride_id))).one_or_none()
        if ride is None or driver is None or trip is None:
            raise HTTPException(status_code=404, detail="Ride or driver not found")
        if ride.driver_id is not None:
            raise HTTPException(status_code=409, detail="Ride already assigned")
        if driver.status != DriverStatus.ONLINE:
            raise HTTPException(status_code=409, detail="Driver not online")
        ride.driver_id = driver_id
        ride.status = RideStatus.DRIVER_ASSIGNED
        driver.status = DriverStatus.BUSY
        trip.status = TripStatus.DRIVER_ASSIGNED

    await clear_offer_async(redis, ride_id=ride_id, driver_id=driver_id)
    notify_event(
        event_type="driver_assigned",
        payload={"ride_id": str(ride.id), "driver_id": str(driver_id)},
    )
    await hub.broadcast(
        hub.ride_channel(ride.id),
        {"type": "driver_assigned", "ride_id": str(ride.id), "driver_id": str(driver_id)},
    )
    await hub.broadcast(
        hub.driver_channel(driver_id),
        {"type": "offer_accepted", "ride_id": str(ride.id)},
    )
    await session.refresh(ride)
    await session.refresh(trip)
    return ride, trip


async def reject_offer(
    *,
    driver_id: uuid.UUID,
    ride_id: uuid.UUID,
) -> None:
    redis = get_redis()
    offer = await get_offer_for_driver_async(redis, driver_id)
    if offer is None or offer.ride_id != ride_id:
        raise HTTPException(status_code=404, detail="No pending offer for this ride")
    await clear_offer_async(redis, ride_id=ride_id, driver_id=driver_id)
    from app.workers.tasks import match_ride

    match_ride.delay(str(ride_id))
