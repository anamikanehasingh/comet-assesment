"""Synchronous Redis client for Celery workers."""

from __future__ import annotations

import redis

_sync: redis.Redis | None = None


def init_redis_sync(url: str) -> None:
    global _sync
    _sync = redis.Redis.from_url(url, decode_responses=True)


def get_redis_sync() -> redis.Redis:
    if _sync is None:
        msg = "sync redis not initialized"
        raise RuntimeError(msg)
    return _sync


def close_redis_sync() -> None:
    global _sync
    if _sync is not None:
        _sync.close()
    _sync = None
