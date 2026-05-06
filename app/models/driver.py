"""Driver ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Index, Numeric
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import DriverStatus, DriverTier

if TYPE_CHECKING:
    from app.models.ride import Ride


class Driver(Base):
    __tablename__ = "drivers"
    __table_args__ = (
        Index("idx_driver_status", "status"),
        Index("idx_driver_tier_status", "tier", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[DriverStatus] = mapped_column(
        SAEnum(DriverStatus, name="driver_status", native_enum=False, length=32),
        nullable=False,
        default=DriverStatus.OFFLINE,
    )
    tier: Mapped[DriverTier] = mapped_column(
        SAEnum(DriverTier, name="driver_tier", native_enum=False, length=32),
        nullable=False,
        default=DriverTier.STANDARD,
    )
    rating: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    last_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    rides: Mapped[list[Ride]] = relationship(back_populates="driver", lazy="selectin")
