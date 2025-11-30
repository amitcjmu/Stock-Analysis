"""
Database Fixtures for Integration Tests

Provides database engine and session fixtures for testing.
"""

from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    # Use in-memory SQLite for fast testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", echo=False, future=True
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture(scope="session")
async def test_session_factory(test_engine):
    """Create test session factory."""
    factory = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    return factory


@pytest.fixture
async def test_session(test_session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async with test_session_factory() as session:
        yield session
        await session.rollback()
