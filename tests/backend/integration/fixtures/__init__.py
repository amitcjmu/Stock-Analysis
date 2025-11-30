"""
Integration Test Fixtures Package

Modular fixture organization for integration testing.
"""

from .db_fixtures import (
    test_engine,
    test_session_factory,
    test_session,
)
from .model_fixtures import (
    test_user,
    test_client,
    test_engagement,
    populated_engagement,
)
from .test_utils import (
    BaseIntegrationTest,
    performance_monitor,
    memory_monitor,
)
from .api_fixtures import (
    api_client,
    frontend_client,
    auth_headers,
    sample_cmdb_csv_content,
    sample_mixed_assets,
    integration_test_config,
)

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
]
