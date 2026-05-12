"""
Database session fixtures for testing with multiple backends.
Supports SQLite (in-memory) and PostgreSQL (via testcontainers).
"""

import pytest
import pytest_asyncio
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def get_base():
    """Lazy import of Base to avoid model registration conflicts."""
    from app_base.base.models.mixin import Base

    return Base


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy for app_tests."""
    import asyncio

    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def async_engine(db_type):
    """Test SQLite async database engine fixture, patch get_async_engine."""
    Base = get_base()

    if not db_type or db_type == "sqlite":
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    elif db_type == "postgresql":
        raise NotImplementedError("PostgreSQL support is not enabled in this fixture.")
    else:
        raise ValueError(f"Unsupported db_type: {db_type}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(name="session_maker")
async def session_maker_fixture(async_engine, monkeypatch: pytest.MonkeyPatch):
    """Create session maker and patch get_session_maker."""
    session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    # Patch get_session_maker to return this test session_maker
    from app_base.core.database import engine as db_engine_mod

    monkeypatch.setattr(db_engine_mod, "get_async_engine", lambda: async_engine)
    monkeypatch.setattr(db_engine_mod, "get_session_maker", lambda: session_maker)
    yield session_maker


@pytest_asyncio.fixture(name="session")
async def session_fixture(session_maker):
    """Create a new database session for testing."""
    async with session_maker() as session:
        yield session
        await session.commit()


@pytest.fixture(name="inspect_session")
async def inspect_session(session_maker):
    """Fixture to provide a session for inspection without committing changes."""
    async with session_maker() as session:
        yield session


# Optional: PostgreSQL support with testcontainers
# Uncomment and install testcontainers-postgres if needed
#
# @pytest_asyncio.fixture(scope="session")
# async def postgres_async_engine():
#     """Fixture to create a PostgreSQL container for async testing."""
#     from testcontainers.postgres import PostgresContainer
#
#     with PostgresContainer("postgres:16") as postgres:
#         url = postgres.get_connection_url().replace("postgresql://", "postgresql+asyncpg://")
#         engine = create_async_engine(url)
#         async with engine.begin() as conn:
#             Base = get_base()
#             await conn.run_sync(Base.metadata.create_all)
#         yield engine
#         async with engine.begin() as conn:
#             await conn.run_sync(Base.metadata.drop_all)
#         await engine.dispose()
