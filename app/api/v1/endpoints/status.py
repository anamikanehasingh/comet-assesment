"""Public status route (example v1 contract)."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.common import StatusResponse

router = APIRouter()


@router.get("/status", response_model=StatusResponse)
async def service_status(request: Request):
    settings = request.app.state.settings
    return StatusResponse(ok=True, service=f"comet-api ({settings.APP_ENV})")
