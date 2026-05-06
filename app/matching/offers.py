"""Pending driver offers stored in Redis with TTL (ride- and driver-scoped keys)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any

from redis.asyncio import Redis as AsyncRedis

from app.matching.constants import offer_key

_DRIVER_INDEX_PREFIX = "comet:offer:driver:"


def _driver_index_key(driver_id: uuid.UUID) -> str:
    return f"{_DRIVER_INDEX_PREFIX}{driver_id}"


@dataclass(frozen=True)
class OfferPayload:
    ride_id: uuid.UUID
    driver_id: uuid.UUID
    token: str

    def to_json(self) -> str:
        return json.dumps(
            {
                "ride_id": str(self.ride_id),
                "driver_id": str(self.driver_id),
                "token": self.token,
            }
        )

    @staticmethod
    def from_json(raw: str) -> OfferPayload:
        data: dict[str, Any] = json.loads(raw)
        return OfferPayload(
            ride_id=uuid.UUID(data["ride_id"]),
            driver_id=uuid.UUID(data["driver_id"]),
            token=str(data["token"]),
        )


async def store_offer_async(
    redis: AsyncRedis,
    *,
    ride_id: uuid.UUID,
    driver_id: uuid.UUID,
    token: str,
    ttl_seconds: int,
) -> None:
    payload = OfferPayload(ride_id=ride_id, driver_id=driver_id, token=token).to_json()
    rkey = offer_key(ride_id)
    dkey = _driver_index_key(driver_id)
    pipe = redis.pipeline(transaction=True)
    pipe.set(rkey, payload, ex=ttl_seconds)
    pipe.set(dkey, str(ride_id), ex=ttl_seconds)
    await pipe.execute()


async def clear_offer_async(redis: AsyncRedis, *, ride_id: uuid.UUID, driver_id: uuid.UUID) -> None:
    pipe = redis.pipeline(transaction=True)
    pipe.delete(offer_key(ride_id))
    pipe.delete(_driver_index_key(driver_id))
    await pipe.execute()


async def get_offer_for_ride_async(redis: AsyncRedis, ride_id: uuid.UUID) -> OfferPayload | None:
    raw = await redis.get(offer_key(ride_id))
    if not raw:
        return None
    return OfferPayload.from_json(raw)


async def get_offer_for_driver_async(
    redis: AsyncRedis,
    driver_id: uuid.UUID,
) -> OfferPayload | None:
    ride_raw = await redis.get(_driver_index_key(driver_id))
    if not ride_raw:
        return None
    ride_id = uuid.UUID(str(ride_raw))
    raw = await redis.get(offer_key(ride_id))
    if not raw:
        return None
    return OfferPayload.from_json(raw)


# --- Sync helpers (Celery worker) ---


def store_offer_sync(
    redis: Any,
    *,
    ride_id: uuid.UUID,
    driver_id: uuid.UUID,
    token: str,
    ttl_seconds: int,
) -> None:
    payload = OfferPayload(ride_id=ride_id, driver_id=driver_id, token=token).to_json()
    rkey = offer_key(ride_id)
    dkey = _driver_index_key(driver_id)
    pipe = redis.pipeline(transaction=True)
    pipe.set(rkey, payload, ex=ttl_seconds)
    pipe.set(dkey, str(ride_id), ex=ttl_seconds)
    pipe.execute()


def clear_offer_sync(redis: Any, *, ride_id: uuid.UUID, driver_id: uuid.UUID) -> None:
    pipe = redis.pipeline(transaction=True)
    pipe.delete(offer_key(ride_id))
    pipe.delete(_driver_index_key(driver_id))
    pipe.execute()


def get_offer_for_ride_sync(redis: Any, ride_id: uuid.UUID) -> OfferPayload | None:
    raw = redis.get(offer_key(ride_id))
    if not raw:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode()
    return OfferPayload.from_json(raw)
