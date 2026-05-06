"""Aggregate v1 routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth_stub,
    auth_token,
    drivers,
    payments,
    pricing,
    reposition,
    rides,
    trips,
)
from app.api.v1.endpoints import status as status_ep
from app.websockets import routes as ws_routes

api_v1_router = APIRouter()

api_v1_router.include_router(status_ep.router, tags=["status"])
api_v1_router.include_router(auth_token.router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(auth_stub.router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(rides.router, tags=["rides"])
api_v1_router.include_router(drivers.router, tags=["drivers"])
api_v1_router.include_router(trips.router, tags=["trips"])
api_v1_router.include_router(pricing.router, tags=["pricing"])
api_v1_router.include_router(payments.router, tags=["payments"])
api_v1_router.include_router(reposition.router, tags=["reposition"])
api_v1_router.include_router(ws_routes.router, tags=["websockets"])
