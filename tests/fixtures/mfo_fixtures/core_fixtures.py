"""
Core pytest fixtures for MFO testing.

Provides essential fixtures for database sessions, request contexts, and service registries.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .base import MockRequestContext, MockServiceRegistry


@pytest.fixture
def demo_tenant_context() -> MockRequestContext:
    """Fixture providing demo tenant context for MFO testing."""
    return MockRequestContext()


@pytest.fixture
def mock_service_registry() -> MockServiceRegistry:
    """Fixture providing mock service registry for MFO operations."""
    return MockServiceRegistry()


@pytest_asyncio.fixture
async def async_db_session():
    """
    Fixture for async database session in MFO tests.

    Uses in-memory SQLite for fast testing with async support.
    """
    # Create in-memory async SQLite engine
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create session factory
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        # In a real test, you would create tables here
        # await create_test_tables(engine)
        yield session
        await session.rollback()

    await engine.dispose()
