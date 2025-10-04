"""
Master Flow Orchestrator (MFO) Test Fixtures

Modularized test fixtures for the Master Flow Orchestrator pattern testing.
Maintains backward compatibility while providing organized fixture components.

Generated with CC for standardized MFO testing infrastructure.
"""

# Preserve backward compatibility - import all public fixtures
from .base import (
    DEMO_CLIENT_ACCOUNT_ID,
    DEMO_ENGAGEMENT_ID,
    DEMO_USER_ID,
    DEMO_USER_EMAIL,
    FLOW_TYPES,
    FLOW_STATUSES,
    DISCOVERY_PHASES,
    MockRequestContext,
    MockServiceRegistry,
)

from .core_fixtures import (
    demo_tenant_context,
    mock_service_registry,
    async_db_session,
)

from .flow_fixtures import (
    sample_master_flow_data,
    sample_discovery_flow_data,
    mfo_flow_states,
)

from .agent_fixtures import (
    mock_tenant_scoped_agent_pool,
    mock_flow_execution_results,
)

from .test_data import (
    tenant_isolation_test_data,
    mfo_performance_test_config,
)

from .helpers import (
    create_mock_mfo_context,
    create_linked_flow_data,
    setup_mfo_test_environment,
)

# Backward compatibility alias
mock_async_session = async_db_session

# Public API - maintains existing import structure
__all__ = [
    # Constants
    "DEMO_CLIENT_ACCOUNT_ID",
    "DEMO_ENGAGEMENT_ID",
    "DEMO_USER_ID",
    "DEMO_USER_EMAIL",
    "FLOW_TYPES",
    "FLOW_STATUSES",
    "DISCOVERY_PHASES",
    # Base classes
    "MockRequestContext",
    "MockServiceRegistry",
    # Core fixtures
    "demo_tenant_context",
    "mock_service_registry",
    "async_db_session",
    "mock_async_session",  # Backward compatibility alias
    # Flow fixtures
    "sample_master_flow_data",
    "sample_discovery_flow_data",
    "mfo_flow_states",
    # Agent fixtures
    "mock_tenant_scoped_agent_pool",
    "mock_flow_execution_results",
    # Test data
    "tenant_isolation_test_data",
    "mfo_performance_test_config",
    # Helper functions
    "create_mock_mfo_context",
    "create_linked_flow_data",
    "setup_mfo_test_environment",
]
