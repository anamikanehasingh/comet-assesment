# Demo recording checklist

Use this script to record a short walkthrough (no video file is committed to the repo).

## Prereqs

1. `docker compose up --build` (api + postgres + redis + **worker**).
2. `make docker-migrate`.
3. Open Swagger: `http://127.0.0.1:8000/docs` (or published port).

## Narration outline (≈3–5 minutes)

1. **Health** — `GET /health` shows Postgres + Redis.
2. **Auth** — `POST /api/v1/auth/token` twice: `role=rider` and `role=driver` (distinct UUIDs); copy JWTs.
3. **Driver online** — `POST /api/v1/drivers/{driver_id}/availability` `{ "status": "online" }` with driver token.
4. **Driver location** — `POST /api/v1/drivers/{driver_id}/location` near a fixed lat/lng (e.g. NYC-ish).
5. **Pricing** — `GET /api/v1/pricing/estimate` with pickup/dest query params; mention Haversine + surge hash optional.
6. **Ride** — `POST /api/v1/rides` with bearer rider token + `pickup`/`destination` near driver; show `ride_id` + `trip_id`.
7. **Offer** — `GET /api/v1/drivers/{driver_id}/offers/pending` → `token`.
8. **Accept** — `POST /api/v1/drivers/{driver_id}/accept` body `ride_id` + `token`.
9. **Trip** — `POST /api/v1/trips/{trip_id}/start`, optional `pause`/`resume`, then `end` (fare filled).
10. **Payment** — `POST /api/v1/payments` with `trip_id` + amount (note idempotency header optional).
11. **WebSocket (optional)** — connect `ws://127.0.0.1:8000/api/v1/ws?token=<JWT>&channel=ride:{ride_uuid}` using a WS client; trigger accept/start from Swagger and show message arrival.

## Talking points

- **trip_id vs ride_id** explicitly called out in Swagger tags.
- **Worker** tail logs: `docker compose logs -f worker` to see `matching_offer_issued`.
- **Production gaps**: no multi-instance WS, Haversine not traffic-aware, mock PSP only.
