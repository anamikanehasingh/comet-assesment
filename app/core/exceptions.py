"""API error envelopes and handlers."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.schemas.errors import ErrorEnvelope, ErrorModel


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def error_envelope(
    code: str,
    message: str,
    request: Request | None = None,
    details: Any | None = None,
) -> ErrorEnvelope:
    rid = _request_id(request) if request is not None else None
    return ErrorEnvelope(
        error=ErrorModel(code=code, message=message, request_id=rid, details=details),
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exc_handler(request: Request, exc: StarletteHTTPException):
        envelope = error_envelope(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail) if exc.detail else "HTTP error",
            request=request,
        )
        return JSONResponse(status_code=exc.status_code, content=envelope.model_dump(mode="json"))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        envelope = error_envelope(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            request=request,
            details=jsonable_encoder(exc.errors()),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=envelope.model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        settings = get_settings()
        envelope = error_envelope(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            request=request,
            details={"type": type(exc).__name__} if settings.exposes_internal_errors else None,
        )
        return JSONResponse(status_code=500, content=envelope.model_dump(mode="json"))
