"""
Test configuration and fixtures for backend tests
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Import here to avoid circular imports and database initialization issues
    from app.main import app
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session for tests that don't need real database."""
    from unittest.mock import MagicMock
    return MagicMock()