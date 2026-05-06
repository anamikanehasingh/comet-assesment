from __future__ import annotations

import uuid
from decimal import Decimal

from app.matching.engine import rank_drivers
from app.models.driver import Driver
from app.models.enums import DriverStatus, DriverTier


def test_rank_prefers_closer_tier_match() -> None:
    d_close = uuid.uuid4()
    d_far = uuid.uuid4()
    drivers = {
        d_close: Driver(
            id=d_close,
            status=DriverStatus.ONLINE,
            tier=DriverTier.STANDARD,
            rating=Decimal("4.5"),
        ),
        d_far: Driver(
            id=d_far,
            status=DriverStatus.ONLINE,
            tier=DriverTier.STANDARD,
            rating=Decimal("4.9"),
        ),
    }
    ordered = [(d_close, 1.0), (d_far, 3.0)]
    ranked = rank_drivers(ordered_geo=ordered, drivers=drivers, requested_tier=DriverTier.STANDARD)
    assert ranked[0] == d_close
