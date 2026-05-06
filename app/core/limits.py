"""SlowAPI limiter factory (Redis or in-memory fallback)."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import Settings


def build_limiter(settings: Settings) -> Limiter:
    return Limiter(
        key_func=get_remote_address,
        storage_uri=settings.rate_limit_storage_uri,
        default_limits=["600/hour"],
        enabled=settings.RATE_LIMIT_ENABLED,
    )
