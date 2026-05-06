"""Async SQLAlchemy engine and session — initialized in app lifespan."""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine(database_url: str) -> None:
    """Create pooled async engine and session factory (call once on startup)."""

    global _engine, _session_factory
    _engine = create_async_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False, autoflush=False)


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


def session_factory_or_raise() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        msg = "Database engine not initialized; did lifespan run?"
        raise RuntimeError(msg)
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = session_factory_or_raise()
    async with factory() as session:
        yield session


async def ping_database(session: AsyncSession) -> bool:
    """Cheap liveness probe — does not validate schema migrations."""

    await session.execute(text("SELECT 1"))
    return True
