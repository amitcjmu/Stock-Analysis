"""
Integration Test Configuration

Pytest configuration and fixtures for integration testing with MFO patterns.
Provides shared test infrastructure, database setup, and MFO-aligned utilities.
Imports standardized MFO fixtures and removes duplicate definitions.

Generated with CC for MFO-aligned integration testing.
"""

import os
import sys
from typing import Any, Dict

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path before importing app modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../backend"))

# Import modularized fixtures
from tests.backend.integration.fixtures import (
    # Database fixtures
    test_engine,
    test_session_factory,
    test_session,
    # Model fixtures
    test_user,
    test_client,
    test_engagement,
    populated_engagement,
    # Test utilities
    BaseIntegrationTest,
    performance_monitor,
    memory_monitor,
    # API fixtures
    api_client,
    frontend_client,
    auth_headers,
    sample_cmdb_csv_content,
    sample_mixed_assets,
    integration_test_config,
)

# Import MFO fixtures and standardized testing infrastructure
from tests.fixtures.mfo_fixtures import (
    MockRequestContext,
    MockServiceRegistry,
    demo_tenant_context,
    mock_service_registry,
    async_db_session,  # Renamed from mock_async_session in mfo_fixtures
    sample_master_flow_data,
    sample_discovery_flow_data,
    mock_tenant_scoped_agent_pool,
    mfo_flow_states,
    tenant_isolation_test_data,
    create_mock_mfo_context,
    create_linked_flow_data,
    setup_mfo_test_environment,
    DEMO_CLIENT_ACCOUNT_ID,
    DEMO_ENGAGEMENT_ID,
    DEMO_USER_ID,
    DEMO_USER_EMAIL,
)

# Create alias for backward compatibility
mock_async_session = async_db_session


@pytest.fixture
def mfo_request_context() -> MockRequestContext:
    """Create MockRequestContext for MFO operations with proper tenant scoping."""
    return create_mock_mfo_context()


@pytest.fixture
async def mfo_test_environment(
    mock_async_session: AsyncSession, mfo_request_context: MockRequestContext
) -> Dict[str, Any]:
    """Setup complete MFO test environment with linked flows."""
    return await setup_mfo_test_environment(
        session=mock_async_session, context=mfo_request_context, flow_type="discovery"
    )


# Convenience fixtures combining MFO patterns with integration testing
@pytest.fixture
def integration_mfo_headers(mfo_request_context: MockRequestContext) -> Dict[str, str]:
    """Integration test headers using MFO request context."""
    headers = mfo_request_context.get_headers()
    headers["Content-Type"] = "application/json"
    return headers


# Re-export all fixtures for pytest discovery and convenience
__all__ = [
    # Database fixtures
    "test_engine",
    "test_session_factory",
    "test_session",
    # Model fixtures
    "test_user",
    "test_client",
    "test_engagement",
    "populated_engagement",
    # Test utilities
    "BaseIntegrationTest",
    "performance_monitor",
    "memory_monitor",
    # API fixtures
    "api_client",
    "frontend_client",
    "auth_headers",
    "sample_cmdb_csv_content",
    "sample_mixed_assets",
    "integration_test_config",
    # MFO fixtures
    "demo_tenant_context",
    "mock_service_registry",
    "mock_async_session",
    "sample_master_flow_data",
    "sample_discovery_flow_data",
    "mock_tenant_scoped_agent_pool",
    "mfo_flow_states",
    "tenant_isolation_test_data",
    "mfo_request_context",
    "mfo_test_environment",
    "integration_mfo_headers",
    "MockRequestContext",
    "MockServiceRegistry",
    "create_mock_mfo_context",
    "create_linked_flow_data",
    "setup_mfo_test_environment",
]
