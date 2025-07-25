"""
Tests for the sessions API endpoints.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from app.models.client_account import ClientAccount, Engagement, User
from app.models.data_import_session import DataImportSession, SessionStatus, SessionType
from fastapi import status
from fastapi.testclient import TestClient

from backend.main import app

# Test client
client = TestClient(app)

# Test data
TEST_CLIENT_ACCOUNT = ClientAccount(
    id=uuid4(),
    name="Test Client",
    description="Test Client Description",
    is_active=True,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
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
    updated_at=datetime.now(timezone.utc),
)

TEST_USER = User(
    id=uuid4(),
    email="test@example.com",
    hashed_password="hashed_password",
    full_name="Test User",
    is_active=True,
    is_superuser=False,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)


# Mock authentication
def mock_get_current_user():
    return TEST_USER


app.dependency_overrides[app.dependencies.get_current_user] = mock_get_current_user


@pytest.fixture
def test_session():
    """Create a test session."""
    return DataImportSession(
        id=uuid4(),
        client_account_id=TEST_CLIENT_ACCOUNT.id,
        engagement_id=TEST_ENGAGEMENT.id,
        session_name="test-session",
        session_display_name="Test Session",
        description="Test session",
        status=SessionStatus.ACTIVE,
        is_default=False,
        session_type=SessionType.DATA_IMPORT,
        auto_created=False,
        created_by=TEST_USER.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def test_create_session(test_session, mocker):
    """Test creating a new session via the API."""
    # Mock the session management service
    mock_service = mocker.MagicMock()
    mock_service.create_session.return_value = test_session

    # Replace the dependency
    app.dependency_overrides[
        app.dependencies.get_session_management_service
    ] = lambda: mock_service

    # Make the request
    response = client.post(
        "/sessions",
        json={
            "client_account_id": str(TEST_CLIENT_ACCOUNT.id),
            "engagement_id": str(TEST_ENGAGEMENT.id),
            "session_name": "test-session",
            "session_display_name": "Test Session",
            "description": "Test session",
            "is_default": False,
            "session_type": "data_import",
            "auto_created": False,
        },
    )

    # Verify the response
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["session_name"] == "test-session"
    assert data["session_display_name"] == "Test Session"
    assert data["description"] == "Test session"
    assert data["status"] == "active"

    # Clean up
    app.dependency_overrides = {}


def test_get_session(test_session, mocker):
    """Test getting a session by ID via the API."""
    # Mock the session management service
    mock_service = mocker.MagicMock()
    mock_service.get_session.return_value = test_session

    # Replace the dependency
    app.dependency_overrides[
        app.dependencies.get_session_management_service
    ] = lambda: mock_service

    # Make the request
    session_id = str(test_session.id)
    response = client.get(f"/sessions/{session_id}")

    # Verify the response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == session_id
    assert data["session_name"] == "test-session"

    # Clean up
    app.dependency_overrides = {}


def test_get_default_session(test_session, mocker):
    """Test getting the default session for an engagement via the API."""
    # Mock the session management service
    mock_service = mocker.MagicMock()
    mock_service.get_default_session.return_value = test_session

    # Replace the dependency
    app.dependency_overrides[
        app.dependencies.get_session_management_service
    ] = lambda: mock_service

    # Make the request
    engagement_id = str(TEST_ENGAGEMENT.id)
    response = client.get(f"/sessions/engagement/{engagement_id}/default")

    # Verify the response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(test_session.id)

    # Clean up
    app.dependency_overrides = {}


def test_set_default_session(test_session, mocker):
    """Test setting a session as the default via the API."""
    # Mock the session management service
    mock_service = mocker.MagicMock()
    test_session.is_default = True
    mock_service.set_default_session.return_value = test_session

    # Replace the dependency
    app.dependency_overrides[
        app.dependencies.get_session_management_service
    ] = lambda: mock_service

    # Make the request
    session_id = str(test_session.id)
    response = client.post(f"/sessions/{session_id}/set-default")

    # Verify the response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == session_id
    assert data["is_default"] is True

    # Clean up
    app.dependency_overrides = {}


def test_merge_sessions(test_session, mocker):
    """Test merging two sessions via the API."""
    # Create a second test session
    target_session = DataImportSession(
        id=uuid4(),
        client_account_id=TEST_CLIENT_ACCOUNT.id,
        engagement_id=TEST_ENGAGEMENT.id,
        session_name="target-session",
        session_display_name="Target Session",
        description="Target session",
        status=SessionStatus.ACTIVE,
        is_default=False,
        session_type=SessionType.DATA_IMPORT,
        auto_created=False,
        created_by=TEST_USER.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # Mock the session management service
    mock_service = mocker.MagicMock()
    mock_service.merge_sessions.return_value = target_session

    # Replace the dependency
    app.dependency_overrides[
        app.dependencies.get_session_management_service
    ] = lambda: mock_service

    # Make the request
    response = client.post(
        "/sessions/merge",
        json={
            "source_session_id": str(test_session.id),
            "target_session_id": str(target_session.id),
            "merge_metadata": {"reason": "Test merge"},
        },
    )

    # Verify the response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(target_session.id)

    # Clean up
    app.dependency_overrides = {}
