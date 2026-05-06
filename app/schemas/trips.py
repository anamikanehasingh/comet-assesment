"""Trip lifecycle schemas."""

from __future__ import annotations

from pydantic import BaseModel


class TripResponse(BaseModel):
    trip_id: str
    ride_id: str
    status: str
    fare: float | None = None
