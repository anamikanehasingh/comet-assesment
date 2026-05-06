"""Fare estimation and final fare (Haversine distance approximation)."""

from __future__ import annotations

import math
from typing import Any


def _to_float(coord: dict[str, Any], key: str) -> float:
    v = coord.get(key)
    if v is None:
        msg = f"Missing {key} in coordinate payload"
        raise ValueError(msg)
    return float(v)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1 - a)))
    return r * c


def trip_distance_km(pickup: dict[str, Any], destination: dict[str, Any]) -> float:
    return haversine_km(
        _to_float(pickup, "lat"),
        _to_float(pickup, "lng"),
        _to_float(destination, "lat"),
        _to_float(destination, "lng"),
    )


def estimate_duration_minutes(distance_km: float, average_kmh: float = 22.0) -> float:
    if average_kmh <= 0:
        return 0.0
    return (distance_km / average_kmh) * 60.0


def compute_fare(
    *,
    distance_km: float,
    duration_minutes: float,
    surge_multiplier: float = 1.0,
    base_fare: float = 2.5,
    per_km: float = 1.15,
    per_minute: float = 0.35,
) -> float:
    core = base_fare + (distance_km * per_km) + (duration_minutes * per_minute)
    fare = max(0.0, core) * max(1.0, float(surge_multiplier))
    return round(fare, 2)
