"""Driver API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import DriverStatus


class LocationUpdate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class AvailabilityUpdate(BaseModel):
    status: DriverStatus


class AcceptOfferRequest(BaseModel):
    ride_id: str
    token: str


class RejectOfferRequest(BaseModel):
    ride_id: str


class PendingOfferResponse(BaseModel):
    ride_id: str | None
    token: str | None = None
