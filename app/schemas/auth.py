"""Dev auth token issuance."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.core.security import Role


class TokenRequest(BaseModel):
    subject: uuid.UUID
    role: Role = Field(default="rider")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
