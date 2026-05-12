"""
Integration test configuration.
Provides fixtures for testing with real database connections.

Note: All common fixtures (db, auth, clients, data) are automatically
available from the root tests/conftest.py through pytest's fixture discovery.
"""

import pytest_asyncio
from tests.fixtures.db import get_base
from tests.utils import clean_db_after_test


@pytest_asyncio.fixture(autouse=True)
async def _clean_db_after_integrate_test(async_engine):
    """
    Automatically cleans up the database after each integration test.

    This is an autouse fixture that applies to all app_tests in the integration suite.
    It deletes all data from all tables after each test, ensuring test isolation.
    """
    yield

    Base = get_base()
    tables = reversed(Base.metadata.sorted_tables)

    async with async_engine.connect() as conn:
        await clean_db_after_test(async_engine.url.drivername, tables, conn)
