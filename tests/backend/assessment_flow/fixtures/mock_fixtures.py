"""
Mock fixtures for assessment flow testing.

Mocked services, repositories, and external dependencies for unit testing.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.fixtures.mfo_fixtures import (
    DEMO_CLIENT_ACCOUNT_ID,
    DEMO_ENGAGEMENT_ID,
    DEMO_USER_ID,
    MockRequestContext,
)


@pytest.fixture
def mock_crewai_service():
    """Mock CrewAI service for testing - MFO compliant."""
    service = MagicMock()
    service.client_account_id = DEMO_CLIENT_ACCOUNT_ID

    # Mock async methods
    service.analyze_architecture_minimums = AsyncMock(return_value={"standards": [], "analysis_complete": True})
    service.analyze_application_components = AsyncMock(return_value={"components": {}, "analysis_complete": True})
    service.analyze_tech_debt = AsyncMock(return_value={"debt_score": 0.5, "analysis_complete": True})
    service.recommend_sixr_strategy = AsyncMock(return_value={"strategy": "retain", "confidence": 0.8})

    return service


@pytest.fixture
def mock_flow_context():
    """Mock flow context for unit testing - MFO compliant."""
    context = MagicMock()
    context.flow_id = "test-flow-123"
    context.client_account_id = DEMO_CLIENT_ACCOUNT_ID
    context.engagement_id = DEMO_ENGAGEMENT_ID
    context.user_id = DEMO_USER_ID
    context.db_session = MagicMock()

    # Mock async methods
    context.save_state = AsyncMock()
    context.load_state = AsyncMock(return_value=None)

    return context


@pytest.fixture
def mock_assessment_repository():
    """Mock assessment repository for testing - MFO compliant."""
    # Create a mock that follows the repository pattern
    mock_repo = MagicMock()
    mock_repo.client_account_id = DEMO_CLIENT_ACCOUNT_ID
    mock_repo.engagement_id = DEMO_ENGAGEMENT_ID

    # Mock standard repository methods
    mock_repo.create_assessment_flow = AsyncMock(return_value="test-flow-123")
    mock_repo.get_assessment_flow_state = AsyncMock(return_value=None)
    mock_repo.save_flow_state = AsyncMock()
    mock_repo.save_engagement_architecture_standards = AsyncMock()
    mock_repo.get_engagement_architecture_standards = AsyncMock(return_value=[])
    mock_repo.save_application_components = AsyncMock()
    mock_repo.get_application_components = AsyncMock(return_value=None)
    mock_repo.save_tech_debt_analysis = AsyncMock()
    mock_repo.get_tech_debt_analysis = AsyncMock(return_value=None)
    mock_repo.save_sixr_decisions = AsyncMock()
    mock_repo.get_sixr_decisions = AsyncMock(return_value=None)
    mock_repo.save_user_input = AsyncMock()
    mock_repo.get_user_input = AsyncMock(return_value=None)
    mock_repo.delete_assessment_flow = AsyncMock()
    mock_repo.get_flows_by_engagement = AsyncMock(return_value=[])
    mock_repo.get_flow_statistics = AsyncMock(
        return_value={"total_flows": 0, "flows_by_status": {}, "flows_by_phase": {}}
    )
    mock_repo.search_flows = AsyncMock(return_value=[])

    return mock_repo


@pytest.fixture
def mock_postgres_store():
    """Mock PostgreSQL store for testing - MFO compliant."""
    mock_store = MagicMock()
    mock_store.load_flow_state = AsyncMock(return_value=None)
    mock_store.save_flow_state = AsyncMock()
    mock_store.delete_flow_state = AsyncMock()
    return mock_store
