"""Celery application (Redis broker)."""

from __future__ import annotations

from celery import Celery
from celery.signals import worker_process_init

from app.core.config import Settings


def _broker_url() -> str:
    return Settings().celery_broker_url


celery_app = Celery(
    "comet",
    broker=_broker_url(),
)

celery_app.conf.task_default_queue = "comet"
celery_app.conf.broker_connection_retry_on_startup = True


@worker_process_init.connect
def init_worker_process(**_kwargs) -> None:
    from app.utils.redis_sync import init_redis_sync
    from app.workers.db_sync import init_sync_engine

    settings = Settings()
    init_sync_engine(settings.DATABASE_URL)
    init_redis_sync(settings.REDIS_URL)


import app.workers.tasks  # noqa: E402, F401 — register tasks
