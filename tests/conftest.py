"""
Global Test Configuration

Main pytest configuration file with fixture registration, marker configuration,
and async test support for the migration orchestration system.

Generated with CC for comprehensive test infrastructure.
"""

import asyncio
import os
import sys
from typing import Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

# Import pytest markers configuration
from tests.fixtures.pytest_markers import pytest_configure

# Import MFO fixtures - these will be automatically available in all tests
from tests.fixtures.mfo_fixtures import (
    demo_tenant_context,
    mock_service_registry,
    async_db_session,
    sample_master_flow_data,
    sample_discovery_flow_data,
    mock_tenant_scoped_agent_pool,
    mfo_flow_states,
    mock_flow_execution_results,
    tenant_isolation_test_data,
    mfo_performance_test_config,
    create_mock_mfo_context,
    create_linked_flow_data,
    setup_mfo_test_environment,
)

# Ensure backend is in path for all tests
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


# REMOVED: Custom event_loop fixture (deprecated pattern with pytest-asyncio 1.0.0+)
# The custom event_loop fixture with scope="session" causes "RuntimeError: Event loop is closed"
# when session-scoped async fixtures are used. pytest-asyncio now manages the event loop automatically
# in auto mode (configured in pytest.ini). See: https://github.com/pytest-dev/pytest-asyncio#event_loop-fixture
# Reference: Issue #443, coding-agent-guide.md banned patterns
#
# Previous implementation tried to handle cleanup manually but this conflicts with pytest-asyncio's
# automatic event loop management. With asyncio_mode = auto, pytest-asyncio creates and manages
# event loops per test function automatically, preventing "Event loop is closed" errors.


# FastAPI Test Client
@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    try:
        from main import app
        return TestClient(app)
    except ImportError as e:
        pytest.skip(f"Could not import FastAPI app: {e}")


# Async FastAPI Test Client
@pytest_asyncio.fixture
async def async_client():
    """Create an async test client for the FastAPI app."""
    try:
        from httpx import AsyncClient
        from main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    except ImportError as e:
        pytest.skip(f"Could not import required async client dependencies: {e}")


# Database configuration for tests
@pytest.fixture(scope="session")
def database_url():
    """Database URL for testing - defaults to in-memory SQLite."""
    return os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")


# Environment setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables and configuration."""
    # Set test environment
    os.environ["TESTING"] = "1"
    os.environ["LOG_LEVEL"] = "DEBUG"

    # Disable external API calls in tests by default
    os.environ["DISABLE_EXTERNAL_APIS"] = "1"

    # Use mock LLM responses in tests
    os.environ["USE_MOCK_LLM"] = "1"

    yield

    # Cleanup environment
    test_env_vars = ["TESTING", "LOG_LEVEL", "DISABLE_EXTERNAL_APIS", "USE_MOCK_LLM"]
    for var in test_env_vars:
        os.environ.pop(var, None)


# Performance testing configuration
@pytest.fixture
def performance_threshold():
    """Performance thresholds for test validation."""
    return {
        "api_response_time": 1.0,      # seconds
        "database_query_time": 0.5,    # seconds
        "agent_execution_time": 30.0,  # seconds
        "memory_usage_mb": 256,        # MB
    }


# Test data cleanup
@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """Automatic cleanup of test data after each test."""
    yield
    # Cleanup would happen here in a real implementation
    # For now, we rely on the in-memory database being disposed


# Pytest collection configuration
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add appropriate markers and configuration."""
    for item in items:
        # Add async marker to async test functions
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)

        # Add slow marker to tests that might take longer
        if "performance" in item.name or "load" in item.name or "e2e" in item.name:
            item.add_marker(pytest.mark.slow)

        # Add database marker to tests that use database fixtures
        if any(fixture_name in item.fixturenames for fixture_name in
               ["mock_async_session", "database_url", "async_client"]):
            item.add_marker(pytest.mark.database)

        # Add agent marker to tests that use agent fixtures
        if any(fixture_name in item.fixturenames for fixture_name in
               ["mock_tenant_scoped_agent_pool", "agent"]):
            item.add_marker(pytest.mark.agent)

        # Add mfo marker to tests using MFO fixtures
        if any(fixture_name in item.fixturenames for fixture_name in
               ["demo_tenant_context", "mock_service_registry", "mfo_flow_states"]):
            item.add_marker(pytest.mark.mfo)


# Pytest configuration
def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests"
    )
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests"
    )
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run end-to-end tests"
    )
    parser.addoption(
        "--skip-agent-tests",
        action="store_true",
        default=False,
        help="Skip agent-related tests"
    )


# Test filtering based on command line options
def pytest_runtest_setup(item):
    """Setup function to filter tests based on command line options."""
    # Skip slow tests unless explicitly requested
    if item.get_closest_marker("slow") and not item.config.getoption("--run-slow"):
        pytest.skip("Skipping slow test (use --run-slow to include)")

    # Skip integration tests unless explicitly requested
    if item.get_closest_marker("integration") and not item.config.getoption("--run-integration"):
        pytest.skip("Skipping integration test (use --run-integration to include)")

    # Skip e2e tests unless explicitly requested
    if item.get_closest_marker("e2e") and not item.config.getoption("--run-e2e"):
        pytest.skip("Skipping e2e test (use --run-e2e to include)")

    # Skip agent tests if requested
    if item.get_closest_marker("agent") and item.config.getoption("--skip-agent-tests"):
        pytest.skip("Skipping agent test (--skip-agent-tests specified)")


# Global test session information
@pytest.fixture(scope="session", autouse=True)
def test_session_info(request):
    """Provide information about the current test session."""
    print(f"\n{'='*60}")
    print(f"Starting test session: {request.node.name}")
    print(f"Python path includes backend: {backend_path in sys.path}")
    print(f"Available MFO fixtures: demo_tenant_context, mock_service_registry, mfo_flow_states")
    print(f"Available markers: mfo, legacy, integration, unit, agent, slow, etc.")
    print(f"{'='*60}\n")

    yield

    print(f"\n{'='*60}")
    print(f"Test session completed")
    print(f"{'='*60}\n")
