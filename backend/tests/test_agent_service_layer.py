"""
Unit tests for Agent Service Layer
Tests the synchronous service interface for AI agents
"""

import concurrent.futures
from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.services.agents.agent_service_layer import AgentServiceLayer, get_agent_service


@pytest.fixture
def service_layer():
    """Create service layer instance for testing"""
    return AgentServiceLayer(
        client_account_id="test-client-id",
        engagement_id="test-engagement-id",
        user_id="test-user-id",
    )


def test_service_layer_initialization(service_layer):
    """Test service layer initializes correctly"""
    assert service_layer.context.client_account_id == "test-client-id"
    assert service_layer.context.engagement_id == "test-engagement-id"
    assert service_layer.context.user_id == "test-user-id"
    assert service_layer._metrics["calls_made"] == 0
    assert service_layer._metrics["errors"] == 0


def test_get_agent_service():
    """Test service factory function"""
    service = get_agent_service("client1", "engagement1", "user1")
    assert isinstance(service, AgentServiceLayer)
    assert service.context.client_account_id == "client1"


@patch("app.services.agents.agent_service_layer.DiscoveryFlowRepository")
@patch("app.services.agents.agent_service_layer.AsyncSessionLocal")
def test_get_flow_status_not_found(mock_session, mock_repo, service_layer):
    """Test flow status when flow doesn't exist"""
    # Mock repository to return None (not found)
    mock_repo_instance = Mock()
    mock_repo_instance.get_by_flow_id = AsyncMock(return_value=None)
    mock_repo.return_value = mock_repo_instance

    # Mock database session context manager
    mock_db = AsyncMock()
    mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session.return_value.__aexit__ = AsyncMock(return_value=None)

    result = service_layer.get_flow_status("non-existent-flow-id")

    assert result["status"] == "not_found"
    assert result["flow_exists"] is False
    # The service should return a guidance message about uploading data
    assert "message" in result or "guidance" in result


@patch("app.services.agents.agent_service_layer.DiscoveryFlowRepository")
@patch("app.services.agents.agent_service_layer.AsyncSessionLocal")
def test_get_flow_status_success(mock_session, mock_repo, service_layer):
    """Test successful flow status retrieval"""
    # Mock flow object
    mock_flow = Mock()
    mock_flow.flow_id = "test-flow-id"
    mock_flow.status = "active"
    mock_flow.get_current_phase.return_value = "data_import"
    mock_flow.get_next_phase.return_value = "attribute_mapping"
    mock_flow.progress_percentage = 16.67
    mock_flow.is_complete.return_value = False
    mock_flow.created_at = None
    mock_flow.data_import_completed = True
    mock_flow.attribute_mapping_completed = False
    mock_flow.data_cleansing_completed = False
    mock_flow.inventory_completed = False
    mock_flow.dependencies_completed = False
    mock_flow.tech_debt_completed = False

    # Mock repository
    mock_repo_instance = Mock()
    mock_repo_instance.get_by_flow_id = AsyncMock(return_value=mock_flow)
    mock_repo.return_value = mock_repo_instance

    # Mock database session context manager
    mock_db = AsyncMock()
    mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session.return_value.__aexit__ = AsyncMock(return_value=None)

    result = service_layer.get_flow_status("test-flow-id")

    assert result["status"] == "success"
    assert result["flow_exists"] is True
    assert result["flow"]["flow_id"] == "test-flow-id"
    assert result["flow"]["current_phase"] == "data_import"
    assert result["flow"]["next_phase"] == "attribute_mapping"
    assert result["flow"]["progress"] == 16.67


def test_error_handling(service_layer):
    """Test standardized error handling"""
    error = Exception("Test error message")
    result = service_layer._handle_service_error("test_method", error)

    assert result["status"] == "error"
    assert result["error"] == "Test error message"
    assert result["method"] == "test_method"
    assert "guidance" in result


def test_metrics_tracking(service_layer):
    """Test performance metrics tracking"""
    # Simulate successful call
    service_layer._log_call("test_method", 0.5, True)

    metrics = service_layer.get_metrics()
    assert metrics["calls_made"] == 1
    assert metrics["errors"] == 0
    assert metrics["avg_response_time"] == 0.5

    # Simulate failed call
    service_layer._log_call("test_method", 0.3, False, "Test error")

    metrics = service_layer.get_metrics()
    assert metrics["calls_made"] == 2
    assert metrics["errors"] == 1
    assert metrics["error_rate"] == 0.5
    assert metrics["last_error"] == "Test error"


@patch("app.services.agents.agent_service_layer.DiscoveryFlowRepository")
@patch("app.services.agents.agent_service_layer.AsyncSessionLocal")
def test_validate_phase_transition_success(mock_session, mock_repo, service_layer):
    """Test successful phase transition validation"""
    # Mock flow object
    mock_flow = Mock()
    mock_flow.data_import_completed = True
    mock_flow.attribute_mapping_completed = False
    mock_flow.get_current_phase.return_value = "data_import"

    # Mock repository
    mock_repo_instance = Mock()
    mock_repo_instance.get_by_flow_id = AsyncMock(return_value=mock_flow)
    mock_repo.return_value = mock_repo_instance

    # Mock database session context manager
    mock_db = AsyncMock()
    mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session.return_value.__aexit__ = AsyncMock(return_value=None)

    result = service_layer.validate_phase_transition(
        "test-flow-id", "data_import", "attribute_mapping"
    )

    assert result["status"] == "success"
    assert result["can_transition"] is True
    assert result["valid_transition"] is True
    assert result["prerequisites_met"] is True
    assert len(result["missing_requirements"]) == 0


def test_service_timeout_handling(service_layer):
    """Test timeout handling in service calls"""
    with patch.object(service_layer.executor, "submit") as mock_submit:
        # Mock timeout
        mock_future = Mock()
        mock_future.result.side_effect = concurrent.futures.TimeoutError("Timeout")
        mock_submit.return_value = mock_future

        result = service_layer.get_flow_status("test-flow-id")

        assert result["status"] == "error"
        assert (
            "timeout" in result["error"].lower()
            or "timed out" in result["error"].lower()
        )


# === Phase 3: Data Services Tests ===


def test_get_import_data(service_layer):
    """Test import data retrieval"""
    with patch(
        "app.services.agents.agent_service_layer.DiscoveryFlowRepository"
    ) as mock_repo, patch(
        "app.services.agents.agent_service_layer.AsyncSessionLocal"
    ) as mock_session:

        # Mock flow with data_import_id
        mock_flow = Mock()
        mock_flow.data_import_id = "test-import-id"

        mock_repo_instance = Mock()
        mock_repo_instance.get_by_flow_id = AsyncMock(return_value=mock_flow)
        mock_repo.return_value = mock_repo_instance

        # Mock database session context manager
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock import records
        mock_record = Mock()
        mock_record.id = "record-1"
        mock_record.raw_data = {"hostname": "server1"}
        mock_record.source_system = "vmware"
        mock_record.import_timestamp = None

        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = [
            mock_record
        ]

        result = service_layer.get_import_data("test-flow-id", limit=10)

        assert result["status"] == "success"
        assert result["total_records"] == 1
        assert len(result["raw_data"]) == 1
        assert result["raw_data"][0]["id"] == "record-1"


def test_validate_mappings_success(service_layer):
    """Test successful mapping validation"""
    mappings = {
        "mappings": [
            {"source_field": "hostname", "target_field": "server_name"},
            {"source_field": "ip", "target_field": "ip_address"},
        ]
    }

    result = service_layer.validate_mappings("test-flow-id", mappings)

    assert result["status"] == "success"
    assert result["is_valid"] is True
    assert result["valid_mappings_count"] == 2
    assert len(result["validation_issues"]) == 0


def test_validate_mappings_with_errors(service_layer):
    """Test mapping validation with errors"""
    mappings = {
        "mappings": [
            {"source_field": "", "target_field": "server_name"},  # Empty source
            {"source_field": "ip", "target_field": ""},  # Empty target
            {"source_field": "os1", "target_field": "os"},
            {"source_field": "os2", "target_field": "os"},  # Duplicate target
        ]
    }

    result = service_layer.validate_mappings("test-flow-id", mappings)

    assert result["status"] == "success"
    assert result["is_valid"] is False
    assert result["valid_mappings_count"] == 1
    assert len(result["validation_issues"]) == 3
    assert "Source field cannot be empty" in result["validation_issues"]
    assert "Duplicate target field" in str(result["validation_issues"])


# === Phase 4: Asset Services Tests ===


@patch("app.services.agents.agent_service_layer.DiscoveryFlowRepository")
@patch("app.services.agents.agent_service_layer.AsyncSessionLocal")
def test_get_discovered_assets(mock_session, mock_repo, service_layer):
    """Test discovered assets retrieval"""
    # Mock flow
    mock_flow = Mock()
    mock_flow.flow_id = "test-flow-id"
    mock_flow.client_account_id = "test-client"
    mock_flow.engagement_id = "test-engagement"
    mock_flow.inventory_completed = True

    mock_repo_instance = Mock()
    mock_repo_instance.get_by_flow_id = AsyncMock(return_value=mock_flow)
    mock_repo.return_value = mock_repo_instance

    # Mock database session context manager
    mock_db = AsyncMock()
    mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session.return_value.__aexit__ = AsyncMock(return_value=None)

    # Mock assets
    mock_asset = Mock()
    mock_asset.id = "asset-1"
    mock_asset.name = "Web Server"
    mock_asset.asset_type = "server"
    mock_asset.asset_subtype = "web"
    mock_asset.description = "Main web server"
    mock_asset.status = "active"
    mock_asset.risk_score = 5.0
    mock_asset.complexity_score = 7.0
    mock_asset.migration_strategy = "rehost"
    mock_asset.created_at = None
    mock_asset.metadata = {"os": "linux"}

    mock_db.execute = AsyncMock()
    mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_asset]

    result = service_layer.get_discovered_assets("test-flow-id")

    assert result["status"] == "success"
    assert result["total_assets"] == 1
    assert len(result["assets"]) == 1
    assert result["assets"][0]["name"] == "Web Server"
    assert result["assets"][0]["type"] == "server"
    assert result["asset_types"]["server"] == 1


def test_get_tech_debt_analysis(service_layer):
    """Test tech debt analysis retrieval"""
    with patch(
        "app.services.agents.agent_service_layer.DiscoveryFlowRepository"
    ) as mock_repo, patch(
        "app.services.agents.agent_service_layer.AsyncSessionLocal"
    ) as mock_session:

        # Mock flow with tech debt data
        mock_flow = Mock()
        mock_flow.tech_debt_completed = True
        mock_flow.crewai_state_data = {
            "tech_debt": {
                "total_score": 85.5,
                "debt_items": [
                    {"name": "Legacy API", "risk_level": "high", "score": 9.0},
                    {"name": "Old Database", "risk_level": "medium", "score": 6.0},
                ],
                "recommendations": ["Modernize API", "Upgrade database"],
                "summary": "High tech debt detected",
            }
        }

        mock_repo_instance = Mock()
        mock_repo_instance.get_by_flow_id = AsyncMock(return_value=mock_flow)
        mock_repo.return_value = mock_repo_instance

        # Mock database session context manager
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session.return_value.__aexit__ = AsyncMock(return_value=None)

        result = service_layer.get_tech_debt_analysis("test-flow-id")

        assert result["status"] == "success"
        assert result["tech_debt_completed"] is True
        assert result["total_debt_score"] == 85.5
        assert result["debt_items_count"] == 2
        assert len(result["high_risk_items"]) == 1
        assert result["high_risk_items"][0]["name"] == "Legacy API"


def test_service_performance_metrics(service_layer):
    """Test performance metrics tracking across multiple calls"""
    # Make several service calls
    service_layer._log_call("test_method_1", 0.1, True)
    service_layer._log_call("test_method_2", 0.2, True)
    service_layer._log_call("test_method_3", 0.05, False, "Test error")

    metrics = service_layer.get_metrics()

    assert metrics["calls_made"] == 3
    assert metrics["errors"] == 1
    assert metrics["error_rate"] == 1 / 3
    assert metrics["avg_response_time"] == (0.1 + 0.2 + 0.05) / 3
    assert metrics["last_error"] == "Test error"
    assert "context" in metrics


if __name__ == "__main__":
    pytest.main([__file__])
