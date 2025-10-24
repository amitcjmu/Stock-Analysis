"""
Shared fixtures for Collection Flow integration tests.
"""

import os
from typing import AsyncIterator

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def async_client() -> AsyncIterator[AsyncClient]:
    """Create async HTTP client for API testing.

    Uses the running Docker backend service for integration testing.
    Timeout set to 180s to accommodate agent LLM calls and file analysis operations.
    """
    base_url = os.getenv("DOCKER_API_BASE", "http://localhost:8000")

    async with AsyncClient(base_url=base_url, timeout=180.0) as client:
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


@pytest.fixture
def auth_headers(
    test_client_account_id: str, test_engagement_id: str, test_user_id: str
) -> dict:
    """Standard authentication headers for collection endpoints."""
    return {
        "X-Client-Account-ID": test_client_account_id,
        "X-Engagement-ID": test_engagement_id,
        "X-User-ID": test_user_id,
    }
