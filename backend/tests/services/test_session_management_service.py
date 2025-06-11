"""
Tests for the SessionManagementService class.
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.data_import_session import DataImportSession, SessionStatus, SessionType
from app.models.client_account import ClientAccount, Engagement
from app.models.user import User
from app.services.session_management_service import SessionManagementService
from app.core.database import Base, async_session_factory

# Test data
TEST_CLIENT_ACCOUNT = ClientAccount(
    id=uuid4(),
    name="Test Client",
    description="Test Client Description",
    is_active=True,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc)
)

TEST_ENGAGEMENT = Engagement(
    id=uuid4(),
    client_account_id=TEST_CLIENT_ACCOUNT.id,
    name="Test Engagement",
    description="Test Engagement Description",
    start_date=datetime.now(timezone.utc),
    end_date=datetime.now(timezone.utc) + timedelta(days=30),
    is_active=True,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc)
)

TEST_USER = User(
    id=uuid4(),
    email="test@example.com",
    hashed_password="hashed_password",
    full_name="Test User",
    is_active=True,
    is_superuser=False,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc)
)

@pytest.fixture
async def db_session():
    """Create a new database session for testing."""
    async with async_session_factory() as session:
        # Add test data
        session.add(TEST_CLIENT_ACCOUNT)
        session.add(TEST_ENGAGEMENT)
        session.add(TEST_USER)
        await session.commit()
        
        yield session
        
        # Clean up
        await session.rollback()

@pytest.fixture
def session_service(db_session: AsyncSession) -> SessionManagementService:
    """Create a SessionManagementService instance with a test database session."""
    return SessionManagementService(db_session)

@pytest.mark.asyncio
async def test_create_session(session_service: SessionManagementService, db_session: AsyncSession):
    """Test creating a new session."""
    # Create a new session
    session = await session_service.create_session(
        client_account_id=str(TEST_CLIENT_ACCOUNT.id),
        engagement_id=str(TEST_ENGAGEMENT.id),
        session_name="test-session",
        description="Test session",
        is_default=True,
        created_by=TEST_USER.id
    )
    
    # Verify the session was created with the correct values
    assert session is not None
    assert session.session_name == "test-session"
    assert session.description == "Test session"
    assert session.is_default is True
    assert session.status == SessionStatus.ACTIVE
    assert session.client_account_id == TEST_CLIENT_ACCOUNT.id
    assert session.engagement_id == TEST_ENGAGEMENT.id
    assert session.created_by == TEST_USER.id
    
    # Verify the session was saved to the database
    result = await db_session.execute(
        select(DataImportSession)
        .where(DataImportSession.id == session.id)
    )
    db_session_obj = result.scalar_one_or_none()
    assert db_session_obj is not None
    assert db_session_obj.session_name == "test-session"

@pytest.mark.asyncio
async def test_get_default_session(session_service: SessionManagementService):
    """Test getting the default session for an engagement."""
    # Create a default session
    session = await session_service.create_session(
        client_account_id=str(TEST_CLIENT_ACCOUNT.id),
        engagement_id=str(TEST_ENGAGEMENT.id),
        is_default=True,
        created_by=TEST_USER.id
    )
    
    # Get the default session
    default_session = await session_service.get_default_session(str(TEST_ENGAGEMENT.id))
    
    # Verify the correct session was returned
    assert default_session is not None
    assert default_session.id == session.id
    assert default_session.is_default is True

@pytest.mark.asyncio
async def test_set_default_session(session_service: SessionManagementService):
    """Test setting a session as the default."""
    # Create two sessions
    session1 = await session_service.create_session(
        client_account_id=str(TEST_CLIENT_ACCOUNT.id),
        engagement_id=str(TEST_ENGAGEMENT.id),
        is_default=True,
        created_by=TEST_USER.id
    )
    
    session2 = await session_service.create_session(
        client_account_id=str(TEST_CLIENT_ACCOUNT.id),
        engagement_id=str(TEST_ENGAGEMENT.id),
        is_default=False,
        created_by=TEST_USER.id
    )
    
    # Set the second session as default
    updated_session = await session_service.set_default_session(str(session2.id))
    
    # Verify the second session is now default
    assert updated_session.is_default is True
    
    # Verify the first session is no longer default
    result = await session_service.db.execute(
        select(DataImportSession)
        .where(DataImportSession.id == session1.id)
    )
    session1_updated = result.scalar_one()
    assert session1_updated.is_default is False

@pytest.mark.asyncio
async def test_merge_sessions(session_service: SessionManagementService, db_session: AsyncSession):
    """Test merging two sessions."""
    # Create two sessions to merge
    session1 = await session_service.create_session(
        client_account_id=str(TEST_CLIENT_ACCOUNT.id),
        engagement_id=str(TEST_ENGAGEMENT.id),
        session_name="source-session",
        created_by=TEST_USER.id
    )
    
    session2 = await session_service.create_session(
        client_account_id=str(TEST_CLIENT_ACCOUNT.id),
        engagement_id=str(TEST_ENGAGEMENT.id),
        session_name="target-session",
        created_by=TEST_USER.id
    )
    
    # Merge session1 into session2
    merged_session = await session_service.merge_sessions(
        source_session_id=str(session1.id),
        target_session_id=str(session2.id),
        merge_metadata={"reason": "Test merge"}
    )
    
    # Verify the merge was successful
    assert merged_session.id == session2.id
    
    # Verify the source session was updated
    result = await db_session.execute(
        select(DataImportSession)
        .where(DataImportSession.id == session1.id)
    )
    source_session_updated = result.scalar_one()
    assert source_session_updated.parent_session_id == session2.id
    assert source_session_updated.status == SessionStatus.ARCHIVED
    
    # Verify the merge was recorded in the target session's agent_insights
    assert 'merge_history' in merged_session.agent_insights
    assert len(merged_session.agent_insights['merge_history']) == 1
    assert merged_session.agent_insights['merge_history'][0]['merged_session_id'] == str(session1.id)
