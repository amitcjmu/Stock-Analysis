"""
Shared fixtures for Collection Flow integration tests.
"""

import pytest
from httpx import AsyncClient


@pytest.fixture
async def async_client() -> AsyncClient:
    """Create async HTTP client for API testing."""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_client_account_id() -> str:
    """Standard test client account ID."""
    return "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def test_engagement_id() -> str:
    """Standard test engagement ID."""
    return "22222222-2222-2222-2222-222222222222"


@pytest.fixture
def test_user_id() -> str:
    """Standard test user ID."""
    return "test-user-123"
