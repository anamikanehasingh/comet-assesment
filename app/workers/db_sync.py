"""Synchronous SQLAlchemy session factory for Celery workers."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

_engine = None
_factory: sessionmaker[Session] | None = None


def init_sync_engine(database_url: str) -> None:
    global _engine, _factory
    sync_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
    _engine = create_engine(sync_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
    _factory = sessionmaker(bind=_engine, expire_on_commit=False, autoflush=False)


@contextmanager
def sync_session_scope() -> Generator[Session, None, None]:
    if _factory is None:
        msg = "sync engine not initialized"
        raise RuntimeError(msg)
    session = _factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
