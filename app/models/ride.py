"""Ride ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import DriverTier, RideStatus

if TYPE_CHECKING:
    from app.models.driver import Driver
    from app.models.rider import Rider
    from app.models.trip import Trip


class Ride(Base):
    __tablename__ = "rides"
    __table_args__ = (
        Index("idx_ride_status", "status"),
        Index("idx_ride_rider", "rider_id"),
        Index("idx_ride_driver", "driver_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("riders.id", ondelete="CASCADE"), nullable=False
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[RideStatus] = mapped_column(
        SAEnum(RideStatus, name="ride_status", native_enum=False, length=32),
        nullable=False,
        default=RideStatus.REQUESTED,
    )
    pickup: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    destination: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    tier: Mapped[DriverTier] = mapped_column(
        SAEnum(DriverTier, name="ride_tier", native_enum=False, length=32),
        nullable=False,
        default=DriverTier.STANDARD,
    )
    surge_multiplier: Mapped[float | None] = mapped_column(nullable=True)
    surge_zone_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    rider: Mapped[Rider] = relationship(back_populates="rides")
    driver: Mapped[Driver | None] = relationship(back_populates="rides")
    trip: Mapped[Trip | None] = relationship(back_populates="ride", uselist=False)
