"""Dev-only JWT issuance."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.core.security import issue_access_token
from app.schemas.auth import TokenRequest, TokenResponse

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
async def issue_token(body: TokenRequest) -> TokenResponse:
    settings = get_settings()
    if settings.APP_ENV not in ("local", "development"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token issuance disabled outside local/dev",
        )
    token = issue_access_token(subject=body.subject, role=body.role)
    return TokenResponse(access_token=token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
