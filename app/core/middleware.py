"""HTTP middleware: CORS, request/correlation ID, idempotency read-through, access log.

Rate limiting is prepared as a no-op layer; wire SlowAPI or a Redis-backed limiter later.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

from app.core.config import Settings

logger = structlog.get_logger(__name__)


def add_cors_middleware(app, settings: Settings) -> None:
    origins = settings.cors_origin_list
    if not origins:
        origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Ensures ``X-Request-ID`` on request/response and binds structlog context."""

    header_name = "X-Request-ID"

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]):
        incoming = request.headers.get(self.header_name)
        request_id = incoming or str(uuid.uuid4())
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
            response.headers[self.header_name] = request_id
            return response
        finally:
            structlog.contextvars.clear_contextvars()


class IdempotencyHeaderMiddleware(BaseHTTPMiddleware):
    """Reads ``Idempotency-Key`` for downstream handlers (no replay cache yet)."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]):
        key = request.headers.get("Idempotency-Key")
        request.state.idempotency_key = key
        return await call_next(request)


class RateLimitPrepMiddleware(BaseHTTPMiddleware):
    """No-op placeholder — enable ``SlowAPI`` / gateway limits without changing call sites."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]):
        return await call_next(request)


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Minimal access log with correlation ID."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]):
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        request_id = getattr(request.state, "request_id", None)
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 3),
            request_id=request_id,
            client=request.client.host if request.client else None,
        )
        return response


def configure_middleware(app, settings: Settings) -> None:
    """Order: outermost listed first for Starlette ``add_middleware`` (LIFO wrap)."""

    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(RateLimitPrepMiddleware)
    app.add_middleware(IdempotencyHeaderMiddleware)
    app.add_middleware(RequestIdMiddleware)
    add_cors_middleware(app, settings)
