"""
Test fixtures for data import integration tests.

Reuses standard fixtures from enrichment tests for consistency.
"""

import pytest
import pytest_asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client_account import ClientAccount, Engagement, User


@pytest.fixture
def client_account_id() -> UUID:
    """Test client account ID for tenant scoping"""
    return uuid4()


@pytest.fixture
def engagement_id() -> UUID:
    """Test engagement ID for tenant scoping"""
    return uuid4()


@pytest_asyncio.fixture
async def test_client_account(
    async_db_session: AsyncSession, client_account_id: UUID
) -> ClientAccount:
    """Create test client account in database for foreign key constraints."""
    client = ClientAccount(
        id=client_account_id,
        name="Data Import Test Client",
        slug=f"data-import-test-{client_account_id.hex[:8]}",
        industry="Technology",
        company_size="Enterprise",
        headquarters_location="Test City",
        primary_contact_name="Test Contact",
        primary_contact_email="contact@testclient.com",
    )
    async_db_session.add(client)
    await async_db_session.commit()
    await async_db_session.refresh(client)
    return client


@pytest_asyncio.fixture
async def test_user(async_db_session: AsyncSession) -> User:
    """Create test user for engagement foreign key."""
    user_id = uuid4()
    user = User(
        id=user_id,
        username=f"data_import_test_user_{user_id.hex[:8]}",
        email=f"dataimport_{user_id.hex[:8]}@test.com",
        password_hash="test_hash",
        is_active=True,
    )
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_engagement(
    async_db_session: AsyncSession,
    test_user: User,
    test_client_account: ClientAccount,
    engagement_id: UUID,
) -> Engagement:
    """Create test engagement in database for foreign key constraints."""
    engagement = Engagement(
        id=engagement_id,
        name="Data Import Test Engagement",
        slug=f"data-import-test-{engagement_id.hex[:8]}",
        description="Test engagement for data import integration testing",
        client_account_id=test_client_account.id,
        engagement_lead_id=test_user.id,
        status="active",
        engagement_type="migration",
    )
    async_db_session.add(engagement)
    await async_db_session.commit()
    await async_db_session.refresh(engagement)
    return engagement
