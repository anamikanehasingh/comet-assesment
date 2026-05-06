"""Nearby driver search using Redis GEO (async)."""

from __future__ import annotations

import uuid

from redis.asyncio import Redis

from app.matching.constants import DRIVERS_GEO_KEY, driver_geo_member


async def geoadd_driver(redis: Redis, driver_id: uuid.UUID, lng: float, lat: float) -> None:
    await redis.geoadd(DRIVERS_GEO_KEY, (lng, lat, driver_geo_member(driver_id)))


async def georem_driver(redis: Redis, driver_id: uuid.UUID) -> None:
    await redis.zrem(DRIVERS_GEO_KEY, driver_geo_member(driver_id))


async def geosearch_nearby(
    redis: Redis,
    *,
    lng: float,
    lat: float,
    radius_km: float,
    count: int = 20,
) -> list[tuple[str, float]]:
    """Return (member, distance_km) sorted by distance."""

    raw = await redis.geosearch(
        DRIVERS_GEO_KEY,
        longitude=lng,
        latitude=lat,
        unit="km",
        radius=radius_km,
        count=count,
        sort="ASC",
        withdist=True,
    )
    out: list[tuple[str, float]] = []
    for item in raw or []:
        if not item:
            continue
        member, dist = item[0], float(item[1])
        out.append((member, dist))
    return out


def parse_driver_member(member: str) -> uuid.UUID | None:
    if not member.startswith("driver:"):
        return None
    try:
        return uuid.UUID(member.removeprefix("driver:"))
    except ValueError:
        return None
