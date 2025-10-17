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
    Fixture for async database session in integration tests.

    Uses the actual PostgreSQL database running in Docker.
    Allows commits within tests (for integration testing real behavior).
    Note: Data created in tests will persist in the database.
    """
    # Import the actual database session factory from app
    from app.core.database import AsyncSessionLocal

    # Create a session using the actual database connection
    async with AsyncSessionLocal() as session:
        yield session
        # Note: We don't rollback here because integration tests
        # may need to commit data to test real database interactions.
        # Data will be left in the database (acceptable for integration tests)
