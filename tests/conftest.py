"""Pytest configuration."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Generator
from pathlib import Path

os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://comet:comet@127.0.0.1:5432/comet",
    ),
)
os.environ.setdefault(
    "REDIS_URL",
    os.environ.get("TEST_REDIS_URL", "redis://127.0.0.1:6379/15"),
)
os.environ.setdefault("APP_ENV", "local")

import pytest
from fastapi.testclient import TestClient

_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations() -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        cwd=str(_ROOT),
        env=os.environ.copy(),
    )


@pytest.fixture(scope="session", autouse=True)
def _init_sync_infra_for_eager_celery() -> None:
    from app.utils.redis_sync import get_redis_sync, init_redis_sync
    from app.workers.db_sync import init_sync_engine

    init_sync_engine(os.environ["DATABASE_URL"])
    init_redis_sync(os.environ["REDIS_URL"])
    get_redis_sync().flushdb()


@pytest.fixture(scope="session", autouse=True)
def _celery_eager_mode() -> None:
    from app.workers.celery_app import celery_app

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    from app.core.config import reset_settings_cache
    from app.main import app

    reset_settings_cache()
    with TestClient(app) as test_client:
        yield test_client
