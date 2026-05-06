"""Driver APIs."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import DbSession
from app.core.security import driver_id_from_claims, require_driver
from app.matching.offers import get_offer_for_driver_async
from app.schemas.drivers import (
    AcceptOfferRequest,
    AvailabilityUpdate,
    LocationUpdate,
    PendingOfferResponse,
    RejectOfferRequest,
)
from app.services.drivers_service import (
    accept_offer,
    reject_offer,
    set_availability,
    update_location,
)
from app.utils.redis import get_redis

router = APIRouter()


def _require_path_driver(path_driver_id: uuid.UUID, claims: dict) -> None:
    if driver_id_from_claims(claims) != path_driver_id:
        raise HTTPException(status_code=403, detail="Driver path id must match token subject")


@router.post("/drivers/{driver_id}/location")
async def post_location(
    driver_id: uuid.UUID,
    body: LocationUpdate,
    session: DbSession,
    claims: dict = Depends(require_driver),
) -> dict:
    _require_path_driver(driver_id, claims)
    await update_location(session, driver_id=driver_id, lat=body.lat, lng=body.lng)
    return {"ok": True}


@router.post("/drivers/{driver_id}/availability")
async def post_availability(
    driver_id: uuid.UUID,
    body: AvailabilityUpdate,
    session: DbSession,
    claims: dict = Depends(require_driver),
) -> dict:
    _require_path_driver(driver_id, claims)
    d = await set_availability(session, driver_id=driver_id, status_value=body.status)
    return {"id": str(d.id), "status": d.status.value}


@router.post("/drivers/{driver_id}/accept")
async def post_accept(
    driver_id: uuid.UUID,
    body: AcceptOfferRequest,
    session: DbSession,
    claims: dict = Depends(require_driver),
) -> dict:
    _require_path_driver(driver_id, claims)
    ride, trip = await accept_offer(
        session,
        driver_id=driver_id,
        ride_id=uuid.UUID(body.ride_id),
        token=body.token,
    )
    return {"ride_id": str(ride.id), "trip_id": str(trip.id), "status": ride.status.value}


@router.post("/drivers/{driver_id}/reject")
async def post_reject(
    driver_id: uuid.UUID,
    body: RejectOfferRequest,
    claims: dict = Depends(require_driver),
) -> dict:
    _require_path_driver(driver_id, claims)
    await reject_offer(driver_id=driver_id, ride_id=uuid.UUID(body.ride_id))
    return {"ok": True}


@router.get("/drivers/{driver_id}/offers/pending", response_model=PendingOfferResponse)
async def pending_offer(
    driver_id: uuid.UUID,
    claims: dict = Depends(require_driver),
) -> PendingOfferResponse:
    _require_path_driver(driver_id, claims)
    redis = get_redis()
    offer = await get_offer_for_driver_async(redis, driver_id)
    if offer is None:
        return PendingOfferResponse(ride_id=None, token=None)
    return PendingOfferResponse(ride_id=str(offer.ride_id), token=offer.token)
