"""Health check response models."""

from pydantic import BaseModel, Field


class ComponentHealth(BaseModel):
    ok: bool = Field(description="Component is reachable and responsive")


class HealthResponse(BaseModel):
    ok: bool
    checks: dict[str, bool] = Field(description="Per-dependency status flags")
