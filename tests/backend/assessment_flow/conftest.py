"""
Assessment Flow Test Configuration

This module provides backward compatibility by importing from the modularized fixtures.
All fixtures are now organized in the fixtures/ directory while maintaining the same public API.

Generated with CC for MFO-compliant assessment flow testing infrastructure.
"""

# Import all fixtures from modularized structure for backward compatibility
from .fixtures import *  # noqa: F403, F401

# Import pytest configuration functions
from .fixtures.test_config import pytest_configure, pytest_collection_modifyitems

# Re-export key fixtures explicitly for clarity
from .fixtures import (
    # Core fixtures
    event_loop,
    test_engine,
    async_db_session,
    flow_context,

    # Mock fixtures
    mock_crewai_service,
    mock_flow_context,
    mock_assessment_repository,
    mock_postgres_store,

    # Data fixtures
    sample_applications,
    sample_assessment_flow_state,
    sample_architecture_standards,
    sample_application_metadata,
    sample_component_analysis_result,
    sample_sixr_strategy_result,
    sample_engagement_context,

    # Test configuration
    disable_real_crews,
    enable_integration_tests,
    enable_performance_tests,
    anyio_backend,

    # Helpers
    assessment_flow_factory,
    assert_helpers,
)
