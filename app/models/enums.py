"""Domain enumerations."""

from __future__ import annotations

import enum


class DriverStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"


class DriverTier(str, enum.Enum):
    STANDARD = "standard"
    PREMIUM = "premium"


class RideStatus(str, enum.Enum):
    REQUESTED = "requested"
    MATCHING = "matching"
    DRIVER_ASSIGNED = "driver_assigned"
    DRIVER_ARRIVING = "driver_arriving"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TripStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    MATCHING = "MATCHING"
    DRIVER_ASSIGNED = "DRIVER_ASSIGNED"
    DRIVER_ARRIVING = "DRIVER_ARRIVING"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
