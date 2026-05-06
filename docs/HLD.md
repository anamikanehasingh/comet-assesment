# High-level design (HLD)

## Scope

Comet is a **modular monolith** FastAPI service for a multi-region ride-hailing MVP: riders request trips, drivers broadcast location into Redis GEO, a **Celery worker** issues time-boxed offers, drivers accept under **PostgreSQL row locks**, trips run through a **finite state machine**, pricing uses **Haversine distance** + Redis surge cache, and payments use a **mock PSP** with idempotency and retry hooks.

## Components

| Component | Role |
|-----------|------|
| **API (uvicorn)** | REST + WebSockets; JWT auth; SlowAPI rate limiting; publishes domain notifications and WS payloads on hot paths. |
| **PostgreSQL** | System of record: riders, drivers, rides, trips, payments; `SELECT … FOR UPDATE` on drivers/rides during accept. |
| **Redis** | GEO index for online drivers (`comet:drivers:geo`), surge multipliers (`comet:surge:zones` HASH), pending offers + driver index keys, optional assign lock, reposition stub stats. |
| **Celery worker** | Same Docker image as API; sync SQLAlchemy + sync Redis for `match_ride`, payment retry stub, analytics stub. |

## Data flow (happy path)

1. Rider `POST /api/v1/rides` → ride + trip in **MATCHING** → `match_ride` task enqueued (or eager in tests).
2. Worker **GEOSEARCH** near pickup, ranks candidates (distance, tier, rating), writes **offer** JSON to Redis with TTL.
3. Driver `POST …/accept` with ride id + token → transaction locks **ride** + **driver** rows → assigns ride, sets driver **busy**, clears Redis offer → WS `driver_assigned`.
4. Driver/rider apps call trip lifecycle on **`trip_id`**: start → pause/resume → end (fare computed) → `POST /api/v1/payments`.

## Scaling notes (production gaps)

- **WebSocket hub** is **in-process**; horizontal scale needs Redis pub/sub or a dedicated realtime gateway.
- **Matching** is single-queue Celery; shard by region/city and add idempotency on tasks.
- **GEO** is flat; partition GEO keys per region. **GEOSEARCH count** is capped (see LLD); monitor stale members.
- Secrets: rotate `JWT_SECRET_KEY`, use managed Postgres/Redis, TLS termination at ingress.

## Related docs

- [LLD.md](./LLD.md) — modules, locking, Redis keys, FSM.
- [PERFORMANCE.md](./PERFORMANCE.md) — targets, load tests, checklist.
