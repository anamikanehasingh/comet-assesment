# Low-level design (LLD)

## API prefix

All versioned HTTP routes are under **`/api/v1/…`**. WebSocket: **`/api/v1/ws`**.

## Ride vs trip identifiers

- **`ride_id`**: booking created by the rider; used on rider routes (`/rides/...`).
- **`trip_id`**: execution entity with fare + FSM; used on **`/trips/{trip_id}/…`** lifecycle routes.
- Creating a ride creates **one** trip with matching status (`MATCHING`).

## JWT (dev issuer)

- `POST /api/v1/auth/token` (enabled for `local` / `development` only) returns HS256 JWT with claims `sub` (UUID string) and `role` (`rider` | `driver`).
- Protected routes use `Authorization: Bearer <token>`.
- WebSocket: pass **`token`** (and **`channel`**) as query parameters; see `/api/v1/ws`.

## Redis keys (documented strategy)

| Key / pattern | Purpose |
|---------------|---------|
| `comet:drivers:geo` | Redis GEO; **member** = `driver:{uuid}`; **coords** = driver last known position when **online**. Removed when driver goes **offline**. |
| `comet:surge:zones` | HASH: field = zone id (string), value = multiplier (string float). |
| `comet:offer:ride:{ride_id}` | JSON `{"ride_id","driver_id","token"}` with TTL (`MATCHING_OFFER_TTL_SECONDS`). |
| `comet:offer:driver:{driver_id}` | String `ride_id` with same TTL (reverse lookup). |
| `comet:assign:ride:{ride_id}` | Optional short TTL `SETNX` guard during matching bursts. |
| `comet:driver_db_loc:{driver_id}` | Throttle key for persisting lat/lng to Postgres (`DRIVER_LOCATION_DB_THROTTLE_SECONDS`). |
| `comet:reposition:zone_demand` | ZSET stub for suggested zones (see `GET /api/v1/reposition/suggestions`). |

## Idempotency

- `Idempotency-Key` header is read in middleware (`request.state.idempotency_key`).
- **Rides**: unique `rides.idempotency_key`; replay returns the same ride/trip.
- **Payments**: unique `payments.idempotency_key`; replay returns same payment row.

## Active ride invariant

A rider may not open a second ride while one is in `requested|matching|driver_assigned|driver_arriving|in_progress`.

## Locking & double booking

- **Accept**: `async with session.begin()` then  
  `await session.scalars(select(Ride)…with_for_update())` and same for `Driver`.  
  Second accept hits **invalid offer** (cleared) or **ride already assigned** → `409`.
- Optional Redis `SETNX` on `comet:assign:ride:{id}` reduces duplicate matching work.

## Trip state machine

Implemented in `app/services/trip_fsm.py`. Illegal transitions return **409**. Notable allowed shortcuts for demos: **DRIVER_ASSIGNED → IN_PROGRESS** (skip **DRIVER_ARRIVING** if you want a shorter flow).

## Celery

- Broker/result: **Redis** (`CELERY_BROKER_URL` defaults to `REDIS_URL`).
- Task names: `comet.match_ride`, `comet.retry_payment`, `comet.send_notification_stub`, `comet.analytics_stub`.
- Worker entry: `celery -A app.workers.celery_app.celery_app worker -Q comet`.

## Rate limiting

- **SlowAPI** + Redis when `RATE_LIMIT_ENABLED=true` (`memory://` when false). Default rule in code: `600/hour` per IP; tune in `app/core/limits.py`.

## Pricing assumptions

- Straight-line **Haversine** between pickup/destination JSON (`lat`, `lng` required). Not OSRM routing. Duration = distance / assumed average speed (`DEFAULT` ~22 km/h in `app/pricing/service.py`).
