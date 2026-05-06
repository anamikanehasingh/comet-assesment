"""Standard error envelope (Pydantic v2)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorModel(BaseModel):
    code: str = Field(description="Stable machine-readable error code")
    message: str = Field(description="Human-readable summary")
    request_id: str | None = Field(default=None)
    details: Any | None = Field(default=None, description="Optional structured details")


class ErrorEnvelope(BaseModel):
    error: ErrorModel
