"""FastAPI application entrypoint and factory."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI


def _bootstrap_newrelic() -> None:
    """Load New Relic agent when license key is present (env-injected in non-local)."""

    if not os.environ.get("NEW_RELIC_LICENSE_KEY"):
        return
    import newrelic.agent

    newrelic.agent.initialize(config_file=None)


_bootstrap_newrelic()

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.health import router as health_router
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.limits import build_limiter
from app.core.logging import configure_logging
from app.core.middleware import configure_middleware
from app.db.session import dispose_engine, init_engine
from app.utils.redis import close_redis_pool, init_redis_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings

    configure_logging(settings.LOG_LEVEL, settings.LOG_JSON)
    init_engine(settings.DATABASE_URL)
    init_redis_pool(settings.REDIS_URL)

    yield

    await dispose_engine()
    await close_redis_pool()


def create_app() -> FastAPI:
    settings = get_settings()
    limiter = build_limiter(settings)
    app = FastAPI(
        title="Comet API",
        description=(
            "Multi-region ride-hailing modular monolith — rides, matching, trips, "
            "payments, WebSockets."
        ),
        version="0.2.0",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "health", "description": "Liveness/readiness probes"},
            {"name": "status", "description": "Service metadata"},
            {"name": "auth", "description": "JWT (dev token issuer + introspection example)"},
            {"name": "rides", "description": "Rider ride lifecycle"},
            {"name": "drivers", "description": "Driver location, availability, offer response"},
            {"name": "trips", "description": "Trip state machine operations (trip_id in path)"},
            {"name": "pricing", "description": "Fare estimates"},
            {"name": "payments", "description": "Mock PSP + webhooks"},
            {"name": "reposition", "description": "Driver repositioning stub"},
            {"name": "websockets", "description": "Real-time channels (see /api/v1/ws)"},
        ],
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    register_exception_handlers(app)
    configure_middleware(app, settings)
    app.add_middleware(SlowAPIMiddleware)

    app.include_router(health_router)
    app.include_router(api_v1_router, prefix="/api/v1")

    return app


app = create_app()
