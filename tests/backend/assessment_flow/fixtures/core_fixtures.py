"""
Core fixtures for assessment flow testing.

Database sessions, event loops, and basic MFO-compliant infrastructure.
"""

import asyncio
import os
from typing import AsyncGenerator

import pytest

from tests.fixtures.mfo_fixtures import (
    DEMO_CLIENT_ACCOUNT_ID,
    DEMO_ENGAGEMENT_ID,
    DEMO_USER_ID,
)

# Test environment setup - MFO compliant
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "postgresql://test_user:test_pass@localhost:5434/test_assessment_db"
os.environ["MFO_ENABLED"] = "true"
os.environ["TENANT_SCOPED_AGENTS"] = "true"

try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.database import Base
    from app.core.flow_context import FlowContext

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    AsyncSession = object
    FlowContext = object


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip("SQLAlchemy not available")

    database_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://test_user:test_pass@localhost:5434/test_assessment_db",
    )
    engine = create_async_engine(database_url, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def async_db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for testing."""
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip("SQLAlchemy not available")

    async_session_factory = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        # Start transaction that will be rolled back after test
        transaction = await session.begin()
        yield session
        await transaction.rollback()


@pytest.fixture
async def flow_context(async_db_session):
    """Create real flow context with test database - MFO compliant."""
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip("SQLAlchemy not available")

    return FlowContext(
        flow_id="test-flow-123",
        client_account_id=DEMO_CLIENT_ACCOUNT_ID,
        engagement_id=DEMO_ENGAGEMENT_ID,
        user_id=DEMO_USER_ID,
        db_session=async_db_session,
    )
