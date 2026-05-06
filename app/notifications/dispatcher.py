"""Dispatch domain notifications (logs + Celery stubs)."""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


def notify_event(*, event_type: str, payload: dict) -> None:
    """Emit notification — local structlog; worker may fan-out to email/SMS."""

    logger.info("domain_event", event_type=event_type, **payload)
