"""
Shared test fixtures for Collection Flow service tests.

Provides common mocks and fixtures for:
- RequestContext
- AsyncSession (database)
- UUID generation
- Common test data
"""

import pytest
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock

from app.core.context import RequestContext


@pytest.fixture
def test_client_account_id():
    """Standard test client account ID."""
    return UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def test_engagement_id():
    """Standard test engagement ID."""
    return UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def test_user_id():
    """Standard test user ID."""
    return "test-user-123"


@pytest.fixture
def request_context(test_user_id, test_client_account_id, test_engagement_id):
    """Create standard RequestContext for tests."""
    return RequestContext(
        user_id=test_user_id,
        client_account_id=test_client_account_id,
        engagement_id=test_engagement_id,
    )


@pytest.fixture
def mock_async_session():
    """
    Create mock AsyncSession with common methods.

    Provides mocks for:
    - execute()
    - commit()
    - rollback()
    - add()
    - flush()
    """
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def sample_question_ids():
    """Generate sample question IDs for testing."""
    return [uuid4() for _ in range(5)]


@pytest.fixture
def sample_asset_ids():
    """Generate sample asset IDs for testing."""
    return [uuid4() for _ in range(10)]


@pytest.fixture
def sample_child_flow_id():
    """Generate sample child flow ID."""
    return uuid4()


# Test data fixtures


@pytest.fixture
def sample_question_rules():
    """Sample question rules data."""
    return [
        {
            "question_id": "app_01_name",
            "question_text": "What is the application name?",
            "question_type": "text",
            "section": "Basic Info",
            "weight": 10,
            "is_required": True,
            "answer_options": None,
        },
        {
            "question_id": "app_02_language",
            "question_text": "What is the programming language?",
            "question_type": "dropdown",
            "section": "Technical",
            "weight": 9,
            "is_required": True,
            "answer_options": ["Java", "Python", "Node.js", ".NET"],
        },
        {
            "question_id": "app_03_database",
            "question_text": "What database does it use?",
            "question_type": "dropdown",
            "section": "Dependencies",
            "weight": 8,
            "is_required": True,
            "answer_options": ["PostgreSQL", "MySQL", "Oracle", "MongoDB"],
        },
    ]


@pytest.fixture
def sample_answers():
    """Sample answer data."""
    return [
        {"question_id": "app_01_name", "answer_value": "Test Application"},
        {"question_id": "app_02_language", "answer_value": "Python"},
    ]


@pytest.fixture
def sample_csv_content():
    """Sample CSV file content for import testing."""
    return b"""Application Name,Language,Version,Database
App1,Python,3.9,PostgreSQL
App2,Java,11,MySQL
App3,Node.js,16,MongoDB
"""


@pytest.fixture
def sample_json_content():
    """Sample JSON file content for import testing."""
    return b"""[
    {"server_name": "server1", "os": "Ubuntu 20.04", "cpu": "8"},
    {"server_name": "server2", "os": "Windows Server", "cpu": "16"}
]"""
