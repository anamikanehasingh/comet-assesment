"""Redis keys and member naming for matching and GEO."""

from __future__ import annotations

import uuid

# Single GEO index for online driver positions. Members: driver:{uuid}
DRIVERS_GEO_KEY = "comet:drivers:geo"

# Surge multipliers per zone id (string float): HGET surge:zones <zone_id>
SURGE_HASH_KEY = "comet:surge:zones"

# Driver repositioning stub stats: zincr demand zone keys
REPOSITION_STATS_KEY = "comet:reposition:zone_demand"


# Optional assignment lock (hot path)
def assign_lock_key(ride_id: uuid.UUID) -> str:
    return f"comet:assign:ride:{ride_id}"


def offer_key(ride_id: uuid.UUID) -> str:
    return f"comet:offer:ride:{ride_id}"


def driver_geo_member(driver_id: uuid.UUID) -> str:
    return f"driver:{driver_id}"
