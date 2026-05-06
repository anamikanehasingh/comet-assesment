"""Shared geo / ride payloads."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import DriverTier


class Place(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    label: str | None = None


class RideCreateRequest(BaseModel):
    pickup: Place
    destination: Place
    tier: DriverTier = DriverTier.STANDARD
    surge_zone_id: str | None = None


class DriverSummary(BaseModel):
    id: str
    status: str
    tier: str
    rating: float | None = None


class RideResponse(BaseModel):
    ride_id: str
    trip_id: str
    status: str
    tier: str
    pickup: dict
    destination: dict
    driver: DriverSummary | None = None
    surge_multiplier: float | None = None
