"""Pricing estimate."""

from __future__ import annotations

from pydantic import BaseModel


class PricingEstimateResponse(BaseModel):
    distance_km: float
    duration_minutes: float
    surge_multiplier: float
    estimated_fare: float
