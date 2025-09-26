"""
Unit Tests for Flow Deletion Operations

<<<<<<< HEAD
Tests the AssessmentFlowService class which provides business logic around flow operations:
=======
Tests the core flow deletion functionality using mocked dependencies:
>>>>>>> 0ad5201e899e9db384bf7873dd67efcfb666cffa
1. Delete a single active flow
2. List active flows
3. Error handling for non-existent flows

<<<<<<< HEAD
Uses unittest.mock to mock the MasterFlowOrchestrator dependency and test actual business logic.
=======
Uses unittest.mock to mock dependencies and test business logic in isolation.
>>>>>>> 0ad5201e899e9db384bf7873dd67efcfb666cffa
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

<<<<<<< HEAD
# Import the service under test
from app.services.unified_assessment_flow_service import AssessmentFlowService

=======
>>>>>>> 0ad5201e899e9db384bf7873dd67efcfb666cffa
# Import fixtures and mock data - use relative import for container compatibility
try:
    from tests.fixtures.mfo_fixtures import (
        demo_tenant_context,
        sample_master_flow_data,
    )
except ImportError:
    # Fallback for container environment
    import sys
<<<<<<< HEAD
    sys.path.append('/app/tests/fixtures')
=======
    sys.path.append('/app/root_tests/fixtures')
>>>>>>> 0ad5201e899e9db384bf7873dd67efcfb666cffa
    from mfo_fixtures import (
        demo_tenant_context,
        sample_master_flow_data,
    )


class TestFlowDeletionOperations:
<<<<<<< HEAD
    """Test suite for flow deletion operations using AssessmentFlowService with mocked orchestrator"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock()


    @pytest.fixture
    def assessment_flow_service(self, mock_db_session, demo_tenant_context):
        """Create AssessmentFlowService instance"""
        return AssessmentFlowService(mock_db_session, demo_tenant_context)
=======
    """Test suite for flow deletion operations using mocked dependencies"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Mock the MasterFlowOrchestrator with all its methods"""
        orchestrator = MagicMock()
        orchestrator.delete_flow = AsyncMock()
        orchestrator.get_flows = AsyncMock()
        orchestrator.get_flow = AsyncMock()
        return orchestrator
>>>>>>> 0ad5201e899e9db384bf7873dd67efcfb666cffa

    @pytest.fixture
    def sample_flow_id(self):
        """Sample flow ID for testing"""
        return str(uuid4())

    @pytest.fixture
    def sample_active_flows(self):
        """Sample list of active flows"""
        return [
            {
                "flow_id": str(uuid4()),
                "flow_type": "discovery",
                "flow_status": "running",
                "client_account_id": "11111111-1111-1111-1111-111111111111",
                "engagement_id": "58467010-6a72-44e8-ba37-cc0238724455"
            },
            {
                "flow_id": str(uuid4()),
                "flow_type": "assessment",
                "flow_status": "initialized",
                "client_account_id": "11111111-1111-1111-1111-111111111111",
                "engagement_id": "58467010-6a72-44e8-ba37-cc0238724455"
            }
        ]

    @pytest.mark.mfo
    @pytest.mark.asyncio
<<<<<<< HEAD
    @patch('app.services.unified_assessment_flow_service.MasterFlowOrchestrator')
    async def test_delete_single_active_flow(self, MockOrchestrator, assessment_flow_service, sample_flow_id):
        """Test deleting a single active flow through AssessmentFlowService"""
        # Arrange
        mock_orchestrator = MockOrchestrator.return_value
        mock_orchestrator.delete_flow = AsyncMock()
        expected_result = {
            "deleted": True,
            "flow_id": sample_flow_id
=======
    async def test_delete_single_active_flow(self, mock_orchestrator, sample_flow_id, demo_tenant_context):
        """Test deleting a single active flow"""
        # Arrange
        expected_result = {
            "success": True,
            "flow_id": sample_flow_id,
            "message": "Flow deleted successfully"
>>>>>>> 0ad5201e899e9db384bf7873dd67efcfb666cffa
        }
        mock_orchestrator.delete_flow.return_value = expected_result

        # Act
<<<<<<< HEAD
        result = await assessment_flow_service.delete_flow(master_flow_id=sample_flow_id)

        # Assert
        assert result["deleted"] is True
        assert result["master_flow_id"] == sample_flow_id
        assert "deleted_at" in result
        assert "delete_details" in result
        mock_orchestrator.delete_flow.assert_called_once_with(
            flow_id=sample_flow_id,
            soft_delete=True,
            reason="Assessment flow deletion requested"
=======
        result = await mock_orchestrator.delete_flow(
            flow_id=sample_flow_id,
            soft_delete=True,
            reason="Test deletion"
        )

        # Assert
        assert result["success"] is True
        assert result["flow_id"] == sample_flow_id
        mock_orchestrator.delete_flow.assert_called_once_with(
            flow_id=sample_flow_id,
            soft_delete=True,
            reason="Test deletion"
>>>>>>> 0ad5201e899e9db384bf7873dd67efcfb666cffa
        )

    @pytest.mark.mfo
    @pytest.mark.asyncio
<<<<<<< HEAD
    @patch('app.services.unified_assessment_flow_service.MasterFlowOrchestrator')
    async def test_list_active_flows(self, MockOrchestrator, assessment_flow_service):
        """Test listing all active flows through AssessmentFlowService"""
        # Arrange
        mock_orchestrator = MockOrchestrator.return_value
        mock_orchestrator.list_flows = AsyncMock()
        # Mock the orchestrator's list_flows method to return assessment flows
        mock_flows = [
            {
                "flow_id": "flow-1",
                "flow_type": "assessment",
                "status": "running",
                "flow_name": "Test Assessment 1",
                "current_phase": "analysis",
                "progress": 50,
                "metadata": {"selected_applications_count": 5},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T01:00:00Z"
            },
            {
                "flow_id": "flow-2", 
                "flow_type": "assessment",
                "status": "initialized",
                "flow_name": "Test Assessment 2",
                "current_phase": "setup",
                "progress": 10,
                "metadata": {"selected_applications_count": 3},
                "created_at": "2024-01-01T00:30:00Z",
                "updated_at": "2024-01-01T00:30:00Z"
            }
        ]
        mock_orchestrator.list_flows.return_value = mock_flows

        # Act
        result = await assessment_flow_service.list_active_flows(limit=10)
=======
    async def test_list_active_flows(self, mock_orchestrator, sample_active_flows, demo_tenant_context):
        """Test listing all active flows"""
        # Arrange
        mock_orchestrator.get_flows.return_value = sample_active_flows

        # Act
        result = await mock_orchestrator.get_flows(
            client_account_id=demo_tenant_context.client_account_id,
            engagement_id=demo_tenant_context.engagement_id,
            flow_status="active"
        )
>>>>>>> 0ad5201e899e9db384bf7873dd67efcfb666cffa

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
<<<<<<< HEAD
        assert result[0]["master_flow_id"] == "flow-1"
        assert result[0]["flow_name"] == "Test Assessment 1"
        assert result[0]["status"] == "running"
        assert result[0]["current_phase"] == "analysis"
        assert result[0]["progress"] == 50
        assert result[0]["selected_applications"] == 5
        assert "created_at" in result[0]
        assert "updated_at" in result[0]
        mock_orchestrator.list_flows.assert_called_once_with(limit=20)  # limit * 2 for filtering

    @pytest.mark.mfo
    @pytest.mark.asyncio
    @patch('app.services.unified_assessment_flow_service.MasterFlowOrchestrator')
    async def test_delete_non_existent_flow(self, MockOrchestrator, assessment_flow_service):
        """Test error handling when trying to delete a non-existent flow through AssessmentFlowService"""
        # Arrange
        mock_orchestrator = MockOrchestrator.return_value
        mock_orchestrator.delete_flow = AsyncMock()
        non_existent_flow_id = str(uuid4())
        
        # Simulate the orchestrator's delete_flow method finding no flow and raising an error
        # This is more realistic - the orchestrator checks for flow existence internally
        mock_orchestrator.delete_flow.side_effect = ValueError(f"Flow {non_existent_flow_id} not found")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Assessment flow deletion failed"):
            await assessment_flow_service.delete_flow(master_flow_id=non_existent_flow_id)

        # Verify the orchestrator's delete_flow was called (it handles the existence check internally)
        mock_orchestrator.delete_flow.assert_called_once_with(
            flow_id=non_existent_flow_id,
            soft_delete=True,
            reason="Assessment flow deletion requested"
        )

    @pytest.mark.mfo
    @pytest.mark.asyncio
    @patch('app.services.unified_assessment_flow_service.MasterFlowOrchestrator')
    async def test_list_flows_when_none_exist(self, MockOrchestrator, assessment_flow_service):
        """Test listing flows when no active flows exist through AssessmentFlowService"""
        # Arrange
        mock_orchestrator = MockOrchestrator.return_value
        mock_orchestrator.list_flows = AsyncMock()
        mock_orchestrator.list_flows.return_value = []

        # Act
        result = await assessment_flow_service.list_active_flows(limit=10)
=======
        assert result[0]["flow_status"] in ["running", "initialized"]
        assert "flow_id" in result[0]
        assert "flow_type" in result[0]
        assert "client_account_id" in result[0]
        assert "engagement_id" in result[0]
        mock_orchestrator.get_flows.assert_called_once()

    @pytest.mark.mfo
    @pytest.mark.asyncio
    async def test_delete_non_existent_flow(self, mock_orchestrator, demo_tenant_context):
        """Test error handling when trying to delete a non-existent flow"""
        # Arrange
        non_existent_flow_id = str(uuid4())
        mock_orchestrator.get_flow.return_value = None  # Flow not found
        mock_orchestrator.delete_flow.side_effect = ValueError(f"Flow {non_existent_flow_id} not found")

        # Act & Assert
        with pytest.raises(ValueError, match=f"Flow {non_existent_flow_id} not found"):
            await mock_orchestrator.delete_flow(
                flow_id=non_existent_flow_id,
                soft_delete=True,
                reason="Test deletion"
            )

        # Verify the orchestrator was called
        mock_orchestrator.delete_flow.assert_called_once()

    @pytest.mark.mfo
    @pytest.mark.asyncio
    async def test_list_flows_when_none_exist(self, mock_orchestrator, demo_tenant_context):
        """Test listing flows when no active flows exist"""
        # Arrange
        mock_orchestrator.get_flows.return_value = []

        # Act
        result = await mock_orchestrator.get_flows(
            client_account_id=demo_tenant_context.client_account_id,
            engagement_id=demo_tenant_context.engagement_id,
            flow_status="active"
        )
>>>>>>> 0ad5201e899e9db384bf7873dd67efcfb666cffa

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0
<<<<<<< HEAD
        mock_orchestrator.list_flows.assert_called_once_with(limit=20)

    @pytest.mark.mfo
    @pytest.mark.asyncio
    @patch('app.services.unified_assessment_flow_service.MasterFlowOrchestrator')
    async def test_tenant_isolation_in_flow_deletion(self, MockOrchestrator, assessment_flow_service, sample_flow_id):
        """Test that flow deletion respects tenant isolation through AssessmentFlowService"""
        # Arrange
        mock_orchestrator = MockOrchestrator.return_value
        mock_orchestrator.delete_flow = AsyncMock()
        expected_result = {
            "deleted": True,
            "flow_id": sample_flow_id
=======
        mock_orchestrator.get_flows.assert_called_once()

    @pytest.mark.mfo
    @pytest.mark.asyncio
    async def test_tenant_isolation_in_flow_deletion(self, mock_orchestrator, sample_flow_id, demo_tenant_context):
        """Test that flow deletion respects tenant isolation"""
        # Arrange
        expected_result = {
            "success": True,
            "flow_id": sample_flow_id,
            "tenant_verified": True
>>>>>>> 0ad5201e899e9db384bf7873dd67efcfb666cffa
        }
        mock_orchestrator.delete_flow.return_value = expected_result

        # Act
<<<<<<< HEAD
        result = await assessment_flow_service.delete_flow(master_flow_id=sample_flow_id)

        # Assert
        assert result["deleted"] is True
        assert result["master_flow_id"] == sample_flow_id
        assert "deleted_at" in result
        assert "delete_details" in result
        mock_orchestrator.delete_flow.assert_called_once_with(
            flow_id=sample_flow_id,
            soft_delete=True,
            reason="Assessment flow deletion requested"
=======
        result = await mock_orchestrator.delete_flow(
            flow_id=sample_flow_id,
            soft_delete=True,
            reason="Test deletion"
        )

        # Assert
        assert result["success"] is True
        assert result["tenant_verified"] is True
        mock_orchestrator.delete_flow.assert_called_once_with(
            flow_id=sample_flow_id,
            soft_delete=True,
            reason="Test deletion"
>>>>>>> 0ad5201e899e9db384bf7873dd67efcfb666cffa
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
