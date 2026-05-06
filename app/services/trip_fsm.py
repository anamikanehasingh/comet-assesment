"""Trip status finite state machine (illegal transitions rejected)."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.models.enums import TripStatus

_ALLOWED: dict[TripStatus, set[TripStatus]] = {
    TripStatus.REQUESTED: {TripStatus.MATCHING, TripStatus.CANCELLED},
    TripStatus.MATCHING: {
        TripStatus.DRIVER_ASSIGNED,
        TripStatus.CANCELLED,
    },
    TripStatus.DRIVER_ASSIGNED: {
        TripStatus.DRIVER_ARRIVING,
        TripStatus.IN_PROGRESS,
        TripStatus.CANCELLED,
    },
    TripStatus.DRIVER_ARRIVING: {
        TripStatus.IN_PROGRESS,
        TripStatus.CANCELLED,
    },
    TripStatus.IN_PROGRESS: {
        TripStatus.PAUSED,
        TripStatus.COMPLETED,
        TripStatus.CANCELLED,
    },
    TripStatus.PAUSED: {
        TripStatus.IN_PROGRESS,
        TripStatus.CANCELLED,
    },
    TripStatus.COMPLETED: set(),
    TripStatus.CANCELLED: set(),
}


def assert_transition(current: TripStatus, new: TripStatus) -> None:
    allowed = _ALLOWED.get(current, set())
    if new not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Illegal trip transition {current.value} -> {new.value}",
        )
