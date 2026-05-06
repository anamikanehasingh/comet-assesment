"""JWT access tokens (HS256) and FastAPI security dependencies."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from app.core.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)

Role = Literal["rider", "driver"]


def issue_access_token(
    *,
    subject: uuid.UUID,
    role: Role,
    expires_minutes: int | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    exp_m = expires_minutes if expires_minutes is not None else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=exp_m)).timestamp()),
        "typ": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["exp", "sub", "role"]},
    )


async def decode_bearer_optional(
    creds: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)],
) -> dict | None:
    if creds is None or not creds.credentials:
        return None
    token = creds.credentials.strip()
    if not token:
        return None
    try:
        return decode_token(token)
    except InvalidTokenError:
        return None


async def require_auth(
    claims: Annotated[dict | None, Depends(decode_bearer_optional)],
) -> dict:
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return claims


async def require_rider(claims: Annotated[dict, Depends(require_auth)]) -> dict:
    if claims.get("role") != "rider":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rider role required")
    return claims


async def require_driver(claims: Annotated[dict, Depends(require_auth)]) -> dict:
    if claims.get("role") != "driver":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Driver role required")
    return claims


def rider_id_from_claims(claims: dict) -> uuid.UUID:
    return uuid.UUID(str(claims["sub"]))


def driver_id_from_claims(claims: dict) -> uuid.UUID:
    return uuid.UUID(str(claims["sub"]))


decode_bearer_stub = decode_bearer_optional


async def get_current_user_optional(
    claims: Annotated[dict | None, Depends(decode_bearer_optional)],
) -> dict | None:
    return claims


async def require_user(claims: Annotated[dict | None, Depends(decode_bearer_optional)]) -> dict:
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return claims
