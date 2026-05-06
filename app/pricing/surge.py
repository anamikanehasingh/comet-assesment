"""Surge multipliers cached in Redis (HASH comet:surge:zones)."""

from __future__ import annotations

from redis.asyncio import Redis

from app.matching.constants import SURGE_HASH_KEY


async def get_surge_multiplier(redis: Redis, zone_id: str | None, default: float = 1.0) -> float:
    if not zone_id:
        return default
    raw = await redis.hget(SURGE_HASH_KEY, zone_id)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default
