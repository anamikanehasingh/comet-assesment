from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.models.enums import TripStatus
from app.services.trip_fsm import assert_transition


def test_allowed_transition() -> None:
    assert_transition(TripStatus.DRIVER_ASSIGNED, TripStatus.IN_PROGRESS)


def test_illegal_transition() -> None:
    with pytest.raises(HTTPException) as exc:
        assert_transition(TripStatus.COMPLETED, TripStatus.IN_PROGRESS)
    assert exc.value.status_code == 409
