"""Background tasks: matching, payments retries, notifications, analytics stub."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select

from app.matching.constants import DRIVERS_GEO_KEY, assign_lock_key
from app.matching.engine import rank_drivers
from app.matching.geo_service import parse_driver_member
from app.matching.offers import store_offer_sync
from app.models.driver import Driver
from app.models.enums import DriverStatus, DriverTier, RideStatus, TripStatus
from app.models.ride import Ride
from app.models.trip import Trip
from app.utils.redis_sync import get_redis_sync
from app.workers.celery_app import celery_app
from app.workers.db_sync import sync_session_scope

logger = structlog.get_logger(__name__)


def _enum_equals(instance, expected) -> bool:
    """ORM may surface Enum or raw string depending on session backend."""

    got = instance.value if hasattr(instance, "value") else str(instance)
    exp = expected.value if hasattr(expected, "value") else str(expected)
    return got == exp


def _geo_candidates_sync(
    redis,
    pickup: dict,
    radius_km: float = 5.0,
) -> list[tuple[uuid.UUID, float]]:
    lng = float(pickup["lng"])
    lat = float(pickup["lat"])
    raw = redis.geosearch(
        DRIVERS_GEO_KEY,
        longitude=lng,
        latitude=lat,
        unit="km",
        radius=radius_km,
        count=100,
        sort="ASC",
        withdist=True,
    )
    out: list[tuple[uuid.UUID, float]] = []
    for item in raw or []:
        if not item:
            continue
        member, dist = item[0], float(item[1])
        did = parse_driver_member(str(member))
        if did:
            out.append((did, dist))
    return out


@celery_app.task(name="comet.match_ride")
def match_ride(ride_id: str) -> None:
    rid = uuid.UUID(ride_id)
    redis = get_redis_sync()
    with sync_session_scope() as session:
        ride = session.scalars(
            select(Ride).where(Ride.id == rid).with_for_update(),
        ).one_or_none()
        if ride is None:
            return
        trip = session.scalars(select(Trip).where(Trip.ride_id == ride.id)).one_or_none()
        if trip is None:
            return
        if not _enum_equals(ride.status, RideStatus.MATCHING) or not _enum_equals(
            trip.status, TripStatus.MATCHING
        ):
            return

        ordered = _geo_candidates_sync(redis, ride.pickup)
        if not ordered:
            logger.info("matching_no_candidates", ride_id=str(ride.id))
            return
        ids = [d for d, _ in ordered]
        drivers = session.scalars(select(Driver).where(Driver.id.in_(ids))).all()
        dmap = {d.id: d for d in drivers}
        tier = ride.tier if isinstance(ride.tier, DriverTier) else DriverTier(str(ride.tier))
        ranked = rank_drivers(ordered_geo=ordered, drivers=dmap, requested_tier=tier)
        chosen: uuid.UUID | None = None
        for cand in ranked:
            drv = dmap.get(cand)
            if drv is None:
                continue
            if not _enum_equals(drv.status, DriverStatus.ONLINE):
                continue
            chosen = cand
            break
        if chosen is None:
            logger.info("matching_no_online_ranked", ride_id=str(ride.id))
            return

        lock_key = assign_lock_key(ride.id)
        if not redis.set(lock_key, str(chosen), nx=True, ex=15):
            logger.info("matching_assign_lock_busy", ride_id=str(ride.id))
            return

        token = str(uuid.uuid4())
        from app.core.config import Settings

        ttl = Settings().MATCHING_OFFER_TTL_SECONDS
        store_offer_sync(
            redis,
            ride_id=ride.id,
            driver_id=chosen,
            token=token,
            ttl_seconds=ttl,
        )
        redis.delete(lock_key)
        logger.info(
            "matching_offer_issued",
            ride_id=str(ride.id),
            driver_id=str(chosen),
        )


@celery_app.task(name="comet.retry_payment")
def retry_payment(payment_id: str) -> None:
    """Stub: mark processing retry in logs — real flow would call PSP."""

    logger.info("payment_retry_stub", payment_id=payment_id)


@celery_app.task(name="comet.send_notification_stub")
def send_notification_stub(event_type: str, payload_json: str) -> None:
    logger.info("notification_enqueue_stub", event_type=event_type, payload=payload_json)


@celery_app.task(name="comet.analytics_stub")
def analytics_stub(name: str) -> None:
    logger.info("analytics_stub", name=name)
