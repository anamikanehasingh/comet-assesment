"""Top-level probes (outside versioned router prefix for load balancers)."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, status
from starlette.responses import JSONResponse

from app.api.deps import DbSession
from app.db.session import ping_database
from app.schemas.health import ComponentHealth, HealthResponse
from app.utils.redis import ping_redis

router = APIRouter()


def _component_json(ok: bool) -> JSONResponse | dict:
    payload = ComponentHealth(ok=ok).model_dump()
    if ok:
        return payload
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)


@router.get("/health/db", tags=["health"])
async def health_db(session: DbSession):
    try:
        ok = await asyncio.wait_for(ping_database(session), timeout=2.0)
    except (TimeoutError, Exception):
        ok = False
    return _component_json(bool(ok))


@router.get("/health/redis", tags=["health"])
async def health_redis():
    try:
        ok = await asyncio.wait_for(ping_redis(), timeout=2.0)
    except (TimeoutError, Exception):
        ok = False
    return _component_json(bool(ok))


@router.get("/health", tags=["health"])
async def health_overall(session: DbSession):
    async def safe_db() -> bool:
        try:
            return await asyncio.wait_for(ping_database(session), timeout=2.0)
        except (TimeoutError, Exception):
            return False

    async def safe_redis() -> bool:
        try:
            return await asyncio.wait_for(ping_redis(), timeout=2.0)
        except (TimeoutError, Exception):
            return False

    db_ok = await safe_db()
    redis_ok = await safe_redis()
    ok = db_ok and redis_ok
    body = HealthResponse(
        ok=ok,
        checks={"database": db_ok, "redis": redis_ok},
    ).model_dump()
    if ok:
        return body
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=body)
