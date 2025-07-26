"""
Assessment Flow Test Configuration

Pytest configuration and fixtures specific to assessment flow testing.
"""

import asyncio
import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Test environment setup
os.environ["ENVIRONMENT"] = "test"
os.environ[
    "DATABASE_URL"
] = "postgresql://test_user:test_pass@localhost:5434/test_assessment_db"

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

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def async_db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip("SQLAlchemy not available")

    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
def mock_crewai_service():
    """Mock CrewAI service for testing."""
    mock = AsyncMock()
    mock.run_crew = AsyncMock()
    mock.is_configured = MagicMock(return_value=True)

    # Default mock responses for different crews
    mock.run_crew.side_effect = lambda crew_name, **kwargs: {
        "architecture_standards_crew": {
            "engagement_standards": [],
            "application_compliance": {},
            "confidence_score": 0.9,
        },
        "component_analysis_crew": {
            "components": [],
            "tech_debt_analysis": [],
            "component_scores": {},
            "overall_tech_debt_score": 5.0,
        },
        "sixr_strategy_crew": {
            "component_treatments": [],
            "overall_strategy": "rehost",
            "confidence_score": 0.8,
        },
        "app_on_page_crew": {"applications_summary": [], "assessment_summary": {}},
    }.get(crew_name, {"status": "completed"})

    return mock


@pytest.fixture
def mock_flow_context():
    """Mock flow context for testing."""
    mock = MagicMock()
    mock.flow_id = "test-flow-123"
    mock.client_account_id = 1
    mock.engagement_id = 1
    mock.user_id = "test-user"
    return mock


@pytest.fixture
async def flow_context(async_db_session):
    """Create real flow context with test database."""
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip("SQLAlchemy not available")

    return FlowContext(
        flow_id="test-flow-123",
        client_account_id=1,
        engagement_id=1,
        user_id="test-user",
        db_session=async_db_session,
    )


@pytest.fixture
def mock_assessment_repository():
    """Mock assessment repository for testing."""
    from tests.fixtures.assessment_fixtures import MockAssessmentRepository

    return MockAssessmentRepository(client_account_id=1)


@pytest.fixture
def mock_postgres_store():
    """Mock PostgreSQL store for testing."""
    from tests.fixtures.assessment_fixtures import MockPostgresStore

    return MockPostgresStore()


@pytest.fixture
def sample_applications():
    """Sample application IDs for testing."""
    return ["app-1", "app-2", "app-3"]


@pytest.fixture
def sample_engagement_context():
    """Sample engagement context data."""
    return {
        "engagement_id": 1,
        "client_account_id": 1,
        "engagement_name": "Test Migration Project",
        "engagement_type": "cloud_migration",
        "target_cloud": "aws",
        "compliance_requirements": ["SOX", "PCI"],
        "business_drivers": ["cost_optimization", "modernization"],
        "timeline_constraints": {
            "project_start": "2025-01-01",
            "go_live_target": "2025-12-31",
        },
    }


@pytest.fixture
def disable_real_crews():
    """Disable real CrewAI crew execution for unit tests."""
    with patch("app.services.crewai_service.get_crewai_service") as mock_service:
        mock_service.return_value = mock_crewai_service()
        yield


@pytest.fixture
def enable_integration_tests():
    """Enable integration tests with real crews."""
    integration_enabled = os.getenv("RUN_INTEGRATION_TESTS", "false").lower() == "true"
    if not integration_enabled:
        pytest.skip("Integration tests disabled")


@pytest.fixture
def enable_performance_tests():
    """Enable performance tests."""
    performance_enabled = os.getenv("RUN_PERFORMANCE_TESTS", "false").lower() == "true"
    if not performance_enabled:
        pytest.skip("Performance tests disabled")


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests with mocked dependencies")
    config.addinivalue_line(
        "markers", "integration: Integration tests with real services"
    )
    config.addinivalue_line("markers", "performance: Performance and load tests")
    config.addinivalue_line(
        "markers", "slow: Slow tests that take more than 30 seconds"
    )


# Collection modifications for different test types
def pytest_collection_modifyitems(config, items):
    """Modify test collection based on environment."""
    os.getenv("ENVIRONMENT", "test")

    # Mark all tests in assessment_flow as unit tests by default
    for item in items:
        if "assessment_flow" in str(item.fspath):
            if not any(
                marker.name in ["integration", "performance"]
                for marker in item.iter_markers()
            ):
                item.add_marker(pytest.mark.unit)

    # Skip slow tests in CI unless explicitly requested
    if os.getenv("CI") and not os.getenv("RUN_SLOW_TESTS"):
        skip_slow = pytest.mark.skip(reason="Slow tests skipped in CI")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


# Test session setup and teardown
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment."""
    # Ensure test environment variables
    os.environ["PYTHONPATH"] = "/app"
    os.environ["ASSESSMENT_FLOW_ENABLED"] = "true"
    os.environ["CREWAI_MOCK_MODE"] = "true"

    yield

    # Cleanup after tests
    # Any session-level cleanup can go here


@pytest.fixture(autouse=True)
def isolate_tests():
    """Ensure test isolation."""
    # Clear any global state between tests
    yield
    # Cleanup after each test


# Async test utilities
@pytest.fixture
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"


# Helper fixtures for common test scenarios
@pytest.fixture
def assessment_flow_factory():
    """Factory for creating assessment flow instances."""

    def _create_flow(flow_id="test-flow", client_account_id=1, engagement_id=1):
        mock_context = MagicMock()
        mock_context.flow_id = flow_id
        mock_context.client_account_id = client_account_id
        mock_context.engagement_id = engagement_id

        # This will be replaced with actual implementation
        mock_flow = MagicMock()
        mock_flow.context = mock_context
        return mock_flow

    return _create_flow


@pytest.fixture
def assert_helpers():
    """Helper functions for common test assertions."""
    from tests.fixtures.assessment_fixtures import (
        assert_flow_state_valid,
        assert_multi_tenant_isolation,
    )

    return {
        "assert_flow_state_valid": assert_flow_state_valid,
        "assert_multi_tenant_isolation": assert_multi_tenant_isolation,
    }
