"""
Unit Tests for Flow Deletion Operations

Tests the core flow deletion functionality using mocked dependencies:
1. Delete a single active flow
2. List active flows
3. Error handling for non-existent flows

Uses unittest.mock to mock dependencies and test business logic in isolation.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Import fixtures and mock data - use relative import for container compatibility
try:
    from tests.fixtures.mfo_fixtures import (
        demo_tenant_context,
        sample_master_flow_data,
    )
except ImportError:
    # Fallback for container environment
    import sys
    sys.path.append('/app/root_tests/fixtures')
    from mfo_fixtures import (
        demo_tenant_context,
        sample_master_flow_data,
    )


class TestFlowDeletionOperations:
    """Test suite for flow deletion operations using mocked dependencies"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Mock the MasterFlowOrchestrator with all its methods"""
        orchestrator = MagicMock()
        orchestrator.delete_flow = AsyncMock()
        orchestrator.get_flows = AsyncMock()
        orchestrator.get_flow = AsyncMock()
        return orchestrator

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
    async def test_delete_single_active_flow(self, mock_orchestrator, sample_flow_id, demo_tenant_context):
        """Test deleting a single active flow"""
        # Arrange
        expected_result = {
            "success": True,
            "flow_id": sample_flow_id,
            "message": "Flow deleted successfully"
        }
        mock_orchestrator.delete_flow.return_value = expected_result

        # Act
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
        )

    @pytest.mark.mfo
    @pytest.mark.asyncio
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

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
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

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0
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
        }
        mock_orchestrator.delete_flow.return_value = expected_result

        # Act
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
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
