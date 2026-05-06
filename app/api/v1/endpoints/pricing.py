"""Pricing estimate."""

from __future__ import annotations

from fastapi import APIRouter

from app.pricing.service import compute_fare, estimate_duration_minutes, trip_distance_km
from app.pricing.surge import get_surge_multiplier
from app.schemas.pricing import PricingEstimateResponse
from app.schemas.rides import Place
from app.utils.redis import get_redis

router = APIRouter()


@router.get("/pricing/estimate", response_model=PricingEstimateResponse)
async def pricing_estimate(
    pickup_lat: float,
    pickup_lng: float,
    dest_lat: float,
    dest_lng: float,
    surge_zone_id: str | None = None,
) -> PricingEstimateResponse:
    redis = get_redis()
    pickup = Place(lat=pickup_lat, lng=pickup_lng).model_dump()
    dest = Place(lat=dest_lat, lng=dest_lng).model_dump()
    dist = trip_distance_km(pickup, dest)
    dur = estimate_duration_minutes(dist)
    surge = await get_surge_multiplier(redis, surge_zone_id, default=1.0)
    fare = compute_fare(distance_km=dist, duration_minutes=dur, surge_multiplier=float(surge))
    return PricingEstimateResponse(
        distance_km=round(dist, 3),
        duration_minutes=round(dur, 2),
        surge_multiplier=float(surge),
        estimated_fare=fare,
    )
