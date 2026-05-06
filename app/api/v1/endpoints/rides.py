"""Rider ride APIs."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.core.security import require_rider, rider_id_from_claims
from app.matching.offers import clear_offer_async, get_offer_for_ride_async
from app.models.ride import Ride
from app.models.trip import Trip
from app.pricing.surge import get_surge_multiplier
from app.schemas.rides import DriverSummary, RideCreateRequest, RideResponse
from app.services.rides import cancel_ride, create_ride, get_ride_for_rider
from app.utils.redis import get_redis

router = APIRouter()


def _ride_out(ride: Ride, trip: Trip | None) -> RideResponse:
    dsummary = None
    if ride.driver:
        dsummary = DriverSummary(
            id=str(ride.driver.id),
            status=ride.driver.status.value,
            tier=ride.driver.tier.value,
            rating=float(ride.driver.rating) if ride.driver.rating is not None else None,
        )
    surge = float(ride.surge_multiplier) if ride.surge_multiplier is not None else None
    return RideResponse(
        ride_id=str(ride.id),
        trip_id=str(trip.id) if trip else "",
        status=ride.status.value,
        tier=ride.tier.value,
        pickup=ride.pickup,
        destination=ride.destination,
        driver=dsummary,
        surge_multiplier=surge,
    )


@router.post("/rides", response_model=RideResponse)
async def post_ride(
    request: Request,
    body: RideCreateRequest,
    session: DbSession,
    claims: dict = Depends(require_rider),
) -> RideResponse:
    redis = get_redis()
    rider_id = rider_id_from_claims(claims)
    sm = await get_surge_multiplier(redis, body.surge_zone_id, default=1.0)
    idem = getattr(request.state, "idempotency_key", None)
    pickup = body.pickup.model_dump()
    destination = body.destination.model_dump()
    ride, trip = await create_ride(
        session,
        rider_id=rider_id,
        pickup=pickup,
        destination=destination,
        tier=body.tier,
        surge_zone_id=body.surge_zone_id,
        surge_multiplier=float(sm),
        idempotency_key=idem,
    )
    await session.refresh(ride, attribute_names=["driver"])
    return _ride_out(ride, trip)


@router.get("/rides/{ride_id}", response_model=RideResponse)
async def get_ride_detail(
    ride_id: uuid.UUID,
    session: DbSession,
    claims: dict = Depends(require_rider),
) -> RideResponse:
    rider_id = rider_id_from_claims(claims)
    stmt = (
        select(Ride)
        .where(Ride.id == ride_id, Ride.rider_id == rider_id)
        .options(selectinload(Ride.driver))
    )
    ride = await session.scalar(stmt)
    if ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")
    trip = await session.scalar(select(Trip).where(Trip.ride_id == ride.id))
    return _ride_out(ride, trip)


@router.post("/rides/{ride_id}/cancel", response_model=RideResponse)
async def post_cancel_ride(
    ride_id: uuid.UUID,
    session: DbSession,
    claims: dict = Depends(require_rider),
) -> RideResponse:
    rider_id = rider_id_from_claims(claims)
    ride = await get_ride_for_rider(session, ride_id=ride_id, rider_id=rider_id)
    trip = await session.scalar(select(Trip).where(Trip.ride_id == ride.id))
    redis = get_redis()
    offer = await get_offer_for_ride_async(redis, ride.id)
    if offer:
        await clear_offer_async(redis, ride_id=ride.id, driver_id=offer.driver_id)
    await cancel_ride(session, ride, trip)
    await session.refresh(ride, attribute_names=["driver"])
    return _ride_out(ride, trip)
