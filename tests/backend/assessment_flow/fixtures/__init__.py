"""
Assessment Flow Test Fixtures

Modularized fixtures for assessment flow testing with MFO compliance.
Maintains backward compatibility while providing organized fixture components.

Generated with CC for standardized assessment flow testing infrastructure.
"""

# Import all fixtures to maintain backward compatibility
from .core_fixtures import (
    event_loop,
    test_engine,
    async_db_session,
    flow_context,
)

from .mock_fixtures import (
    mock_crewai_service,
    mock_flow_context,
    mock_assessment_repository,
    mock_postgres_store,
)

from .data_fixtures import (
    sample_applications,
    sample_assessment_flow_state,
    sample_architecture_standards,
    sample_application_metadata,
    sample_component_analysis_result,
    sample_sixr_strategy_result,
    sample_engagement_context,
)

from .test_config import (
    disable_real_crews,
    enable_integration_tests,
    enable_performance_tests,
    anyio_backend,
)

from .helpers import (
    assessment_flow_factory,
    assert_helpers,
)

# Public API
__all__ = [
    # Core fixtures
    "event_loop",
    "test_engine",
    "async_db_session",
    "flow_context",
    # Mock fixtures
    "mock_crewai_service",
    "mock_flow_context",
    "mock_assessment_repository",
    "mock_postgres_store",
    # Data fixtures
    "sample_applications",
    "sample_assessment_flow_state",
    "sample_architecture_standards",
    "sample_application_metadata",
    "sample_component_analysis_result",
    "sample_sixr_strategy_result",
    "sample_engagement_context",
    # Test configuration
    "disable_real_crews",
    "enable_integration_tests",
    "enable_performance_tests",
    "anyio_backend",
    # Helpers
    "assessment_flow_factory",
    "assert_helpers",
]
