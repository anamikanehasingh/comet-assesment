# Performance targets & measurement

## Targets (MVP / best-effort)

| Area | Target | How measured (MVP) |
|------|--------|---------------------|
| Driver location ingest | &lt; 100 ms p99 API latency | APM (New Relic) or load tool on `POST /drivers/{id}/location` |
| WS status propagation | &lt; 500 ms | Time from HTTP accept/start/end until WS client receives payload (single-node hub; not production-grade) |
| Matching round-trip | &lt; 2 s to first offer | Worker logs `matching_offer_issued`; subtract ride `created_at` |
| PostgreSQL | No duplicate driver on concurrent accept | Integration test `tests/test_concurrent_accept.py` |

## Load testing

Add dev dependency if needed: `pip install locust`.

```bash
# API on localhost:8000 with valid JWTs — edit Locust file hosts/headers as needed
locust -f scripts/load/locustfile.py --host=http://127.0.0.1:8000
```

Docker Compose: publish API port, run Locust on the host.

## Optimization checklist

1. Enable `RATE_LIMIT_ENABLED` + Redis in staging; tune `default_limits` in `app/core/limits.py`.
2. Increase Celery concurrency: `celery worker -c 4` (measure DB pool sizes).
3. Expand **GEOSEARCH count** / pre-filter inactive drivers in SQL before ranking.
4. Replace in-memory WS hub with Redis pub/sub fan-out.
5. Add Beat + dead-letter for offer expiry retries (currently reject-driven retry; TTL expiry is a documented gap).

## Coverage

CI runs `pytest --cov=app --cov-fail-under=65`. Latest local measurement (Docker `checks` profile): **~75%** total `app/` package after test suite expansion.
