"""Ranking helpers for driver matching."""

from __future__ import annotations

import uuid

from app.models.driver import Driver
from app.models.enums import DriverTier


def score_candidate(
    *,
    distance_km: float,
    driver: Driver,
    requested_tier: DriverTier,
) -> float:
    """Lower is better. Tier mismatch adds penalty; higher rating helps."""

    tier_penalty = 0.0 if driver.tier == requested_tier else 2.5
    rating = float(driver.rating) if driver.rating is not None else 3.0
    rating_term = (5.0 - min(max(rating, 0.0), 5.0)) * 0.15
    return distance_km * 1.0 + tier_penalty + rating_term


def rank_drivers(
    *,
    ordered_geo: list[tuple[uuid.UUID, float]],
    drivers: dict[uuid.UUID, Driver],
    requested_tier: DriverTier,
) -> list[uuid.UUID]:
    candidates: list[tuple[uuid.UUID, float]] = []
    for did, dist in ordered_geo:
        drv = drivers.get(did)
        if drv is None:
            continue
        s = score_candidate(distance_km=dist, driver=drv, requested_tier=requested_tier)
        candidates.append((did, s))
    candidates.sort(key=lambda x: x[1])
    return [c[0] for c in candidates]
