"""Common response models for public APIs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StatusResponse(BaseModel):
    ok: bool = True
    service: str = Field(default="comet-api")
