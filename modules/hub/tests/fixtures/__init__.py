"""
Centralized fixtures package.
Import all fixtures from this package for easy access.
"""

from tests.fixtures.clients import (
    AsyncClientWithJson,
    app_fixture,
    client_fixture,
)
from tests.fixtures.db import (
    async_engine,
    event_loop_policy,
    inspect_session,
    session_fixture,
    session_maker_fixture,
)

__all__ = [
    # Database fixtures
    "event_loop_policy",
    "async_engine",
    "session_maker_fixture",
    "session_fixture",
    "inspect_session",
    # Client fixtures
    "AsyncClientWithJson",
    "app_fixture",
    "client_fixture",
    # Auth fixtures (add auth fixtures here when available)
]
