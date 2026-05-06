from __future__ import annotations

from app.pricing.service import compute_fare, haversine_km, trip_distance_km


def test_haversine_known_distance() -> None:
    # ~1 km-ish in Manhattan grid approximation
    d = haversine_km(40.73, -73.99, 40.74, -73.99)
    assert 1.0 < d < 1.5


def test_trip_distance_and_fare() -> None:
    pickup = {"lat": 40.73, "lng": -73.99}
    dest = {"lat": 40.75, "lng": -73.98}
    dist = trip_distance_km(pickup, dest)
    fare = compute_fare(distance_km=dist, duration_minutes=10.0, surge_multiplier=1.0)
    assert dist > 0
    assert fare > 0
