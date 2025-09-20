"""
Test configuration fixtures for assessment flow testing.

Environment setup, test markers, and configuration utilities.
"""

import os
from unittest.mock import patch

import pytest

from .mock_fixtures import mock_crewai_service, mock_tenant_scoped_agent_pool


@pytest.fixture
def disable_real_crews():
    """Disable real CrewAI crew execution for unit tests - use TenantScopedAgentPool."""
    with patch("app.services.persistent_agents.TenantScopedAgentPool") as mock_pool_class:
        mock_pool = mock_tenant_scoped_agent_pool()
        mock_pool_class.return_value = mock_pool

        with patch("app.services.crewai_service.get_crewai_service") as mock_service:
            mock_service.return_value = mock_crewai_service()
            yield mock_pool


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


@pytest.fixture
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"


# Test markers - inherit from MFO base markers
def pytest_configure(config):
    """Configure pytest markers for assessment flow - MFO compliant."""
    # Import and run base MFO markers
    try:
        from tests.fixtures.pytest_markers import pytest_configure as base_pytest_configure

        base_pytest_configure(config)
    except ImportError:
        pass

    # Add assessment-specific markers
    config.addinivalue_line("markers", "assessment_unit: Unit tests for assessment flow components")
    config.addinivalue_line("markers", "assessment_integration: Integration tests for assessment flow")
    config.addinivalue_line("markers", "assessment_crews: Tests involving assessment CrewAI crews")
    config.addinivalue_line("markers", "architecture_standards: Tests for architecture standards functionality")
    config.addinivalue_line("markers", "tech_debt: Tests for technical debt analysis")
    config.addinivalue_line("markers", "sixr_strategy: Tests for 6R strategy determination")


# Collection modifications for different test types
def pytest_collection_modifyitems(config, items):
    """Modify test collection based on environment - MFO compliant."""
    os.getenv("ENVIRONMENT", "test")

    # Mark all tests in assessment_flow with appropriate MFO markers
    for item in items:
        if "assessment_flow" in str(item.fspath):
            # Add MFO marker by default
            item.add_marker(pytest.mark.mfo)

            # Add assessment_flow marker
            item.add_marker(pytest.mark.assessment_flow)

            # Add unit test marker if no other test type specified
            if not any(marker.name in ["integration", "performance", "e2e"] for marker in item.iter_markers()):
                item.add_marker(pytest.mark.unit)
                item.add_marker(pytest.mark.assessment_unit)

    # Skip slow tests in CI unless explicitly requested
    if os.getenv("CI") and not os.getenv("RUN_SLOW_TESTS"):
        skip_slow = pytest.mark.skip(reason="Slow tests skipped in CI")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


# Test session setup and teardown
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment - MFO compliant."""
    # Ensure test environment variables
    os.environ["PYTHONPATH"] = "/app"
    os.environ["ASSESSMENT_FLOW_ENABLED"] = "true"
    os.environ["CREWAI_MOCK_MODE"] = "true"
    os.environ["MFO_ENABLED"] = "true"
    os.environ["TENANT_SCOPED_AGENTS"] = "true"
    os.environ["USE_PERSISTENT_AGENTS"] = "true"

    yield

    # Cleanup after tests
    # Any session-level cleanup can go here


@pytest.fixture(autouse=True)
def isolate_tests():
    """Ensure test isolation."""
    # Clear any global state between tests
    yield
    # Cleanup after each test
