"""
Master Flow Orchestrator (MFO) Test Fixtures

This module provides backward compatibility by importing from the modularized fixtures.
All fixtures are now organized in the mfo_fixtures/ directory while maintaining the same public API.

Generated with CC for standardized MFO testing infrastructure.
"""

# Import all public fixtures from modularized structure for backward compatibility
from .mfo_fixtures import *  # noqa: F403, F401

# Explicitly re-export for clarity and IDE support
from .mfo_fixtures import (
    # Constants
    DEMO_CLIENT_ACCOUNT_ID,
    DEMO_ENGAGEMENT_ID,
    DEMO_USER_ID,
    DEMO_USER_EMAIL,
    FLOW_TYPES,
    FLOW_STATUSES,
    DISCOVERY_PHASES,

    # Base classes
    MockRequestContext,
    MockServiceRegistry,

    # Core fixtures
    demo_tenant_context,
    mock_service_registry,
    async_db_session,

    # Flow fixtures
    sample_master_flow_data,
    sample_discovery_flow_data,
    mfo_flow_states,

    # Agent fixtures
    mock_tenant_scoped_agent_pool,
    mock_flow_execution_results,

    # Test data
    tenant_isolation_test_data,
    mfo_performance_test_config,

    # Helper functions
    create_mock_mfo_context,
    create_linked_flow_data,
    setup_mfo_test_environment,
)
