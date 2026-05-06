"""Example authenticated route wiring (JWT-ready stub)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import decode_bearer_stub

router = APIRouter()


@router.get("/me")
async def me(
    claims: Annotated[dict | None, Depends(decode_bearer_stub)],
):
    return {"authenticated": claims is not None, "claims": claims}
