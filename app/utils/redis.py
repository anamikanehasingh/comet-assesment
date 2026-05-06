"""Async Redis connection pool and helpers (cache / rate-limit prep)."""

from __future__ import annotations

from redis.asyncio import ConnectionPool, Redis

_pool: ConnectionPool | None = None
_client: Redis | None = None


def init_redis_pool(url: str) -> None:
    global _pool, _client
    _pool = ConnectionPool.from_url(url, decode_responses=True, max_connections=50)
    _client = Redis(connection_pool=_pool)


async def close_redis_pool() -> None:
    global _pool, _client
    if _client is not None:
        await _client.aclose()
    _client = None
    if _pool is not None:
        await _pool.disconnect()
    _pool = None


def get_redis() -> Redis:
    if _client is None:
        msg = "Redis pool not initialized; did lifespan run?"
        raise RuntimeError(msg)
    return _client


async def ping_redis() -> bool:
    return bool(await get_redis().ping())
