"""Smart driver repositioning MVP stub."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import require_driver
from app.matching.constants import REPOSITION_STATS_KEY
from app.utils.redis import get_redis

router = APIRouter()


@router.get("/reposition/suggestions")
async def reposition_suggestions(
    claims: dict = Depends(require_driver),
    limit: int = 5,
) -> dict:
    redis = get_redis()
    zones = await redis.zrevrange(REPOSITION_STATS_KEY, 0, max(0, limit - 1), withscores=True)
    return {
        "zones": [{"zone_id": z, "demand_score": float(score)} for z, score in zones],
        "note": (
            "MVP stub: Redis ZSET comet:reposition:zone_demand (ingest via analytics/matching)."
        ),
    }
