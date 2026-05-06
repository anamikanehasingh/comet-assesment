"""Seed surge + reposition stub stats in Redis (optional local bootstrap)."""

from __future__ import annotations

import os

from app.matching.constants import REPOSITION_STATS_KEY, SURGE_HASH_KEY


def main() -> None:
    import redis

    url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
    r = redis.Redis.from_url(url, decode_responses=True)
    r.hset(SURGE_HASH_KEY, mapping={"downtown": "1.25", "airport": "1.5", "default": "1.0"})
    r.zadd(REPOSITION_STATS_KEY, {"downtown": 120, "airport": 90, "suburbs": 40})
    print("seed: surge HASH + reposition ZSET written")


if __name__ == "__main__":
    main()
