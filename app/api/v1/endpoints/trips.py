"""Trip lifecycle."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.core.security import require_auth
from app.schemas.trips import TripResponse
from app.services.trips import end_trip, pause_trip, resume_trip, start_trip

router = APIRouter(dependencies=[Depends(require_auth)])


@router.post("/trips/{trip_id}/start", response_model=TripResponse)
async def trip_start(trip_id: uuid.UUID, session: DbSession) -> TripResponse:
    trip = await start_trip(session, trip_id)
    return TripResponse(
        trip_id=str(trip.id),
        ride_id=str(trip.ride_id),
        status=trip.status.value,
        fare=float(trip.fare) if trip.fare is not None else None,
    )


@router.post("/trips/{trip_id}/pause", response_model=TripResponse)
async def trip_pause(trip_id: uuid.UUID, session: DbSession) -> TripResponse:
    trip = await pause_trip(session, trip_id)
    return TripResponse(
        trip_id=str(trip.id),
        ride_id=str(trip.ride_id),
        status=trip.status.value,
        fare=float(trip.fare) if trip.fare is not None else None,
    )


@router.post("/trips/{trip_id}/resume", response_model=TripResponse)
async def trip_resume(trip_id: uuid.UUID, session: DbSession) -> TripResponse:
    trip = await resume_trip(session, trip_id)
    return TripResponse(
        trip_id=str(trip.id),
        ride_id=str(trip.ride_id),
        status=trip.status.value,
        fare=float(trip.fare) if trip.fare is not None else None,
    )


@router.post("/trips/{trip_id}/end", response_model=TripResponse)
async def trip_end(trip_id: uuid.UUID, session: DbSession) -> TripResponse:
    trip = await end_trip(session, trip_id)
    return TripResponse(
        trip_id=str(trip.id),
        ride_id=str(trip.ride_id),
        status=trip.status.value,
        fare=float(trip.fare) if trip.fare is not None else None,
    )
