"""
Test CrewAI Flow Service handling of deleted flows

Tests that deleted flows cannot be resumed and proper error handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.crewai_flow_service import CrewAIFlowService
from app.core.exceptions import InvalidFlowStateError
from app.models.discovery_flow import DiscoveryFlow


class TestCrewAIFlowServiceDeletedFlows:
    """Test suite for deleted flow handling in CrewAI Flow Service"""

    @pytest.fixture
    def mock_discovery_flow_service(self):
        """Mock discovery flow service"""
        mock_service = AsyncMock()
        return mock_service

    @pytest.fixture
    def crewai_flow_service(self):
        """Create CrewAI Flow Service instance"""
        return CrewAIFlowService()

    @pytest.fixture
    def deleted_flow(self):
        """Create a mock deleted flow"""
        flow = MagicMock(spec=DiscoveryFlow)
        flow.flow_id = "914ebf01-5174-4efa-9a81-5deb968dac60"
        flow.status = "deleted"
        flow.current_phase = "field_mapping"
        flow.data_import_id = "test-data-import-id"
        return flow

    @pytest.fixture
    def cancelled_flow(self):
        """Create a mock cancelled flow"""
        flow = MagicMock(spec=DiscoveryFlow)
        flow.flow_id = "test-cancelled-flow-id"
        flow.status = "cancelled"
        flow.current_phase = "data_import"
        flow.data_import_id = None
        return flow

    @pytest.mark.asyncio
    async def test_resume_deleted_flow_raises_invalid_flow_state_error(
        self, crewai_flow_service, mock_discovery_flow_service, deleted_flow
    ):
        """Test that attempting to resume a deleted flow raises InvalidFlowStateError"""
        
        # Mock the discovery service to return the deleted flow
        mock_discovery_flow_service.get_flow_by_id.return_value = deleted_flow
        
        # Mock the _get_discovery_flow_service method
        with patch.object(crewai_flow_service, '_get_discovery_flow_service', return_value=mock_discovery_flow_service):
            with patch('app.services.crewai_flow_service.CREWAI_FLOWS_AVAILABLE', True):
                # Attempt to resume the deleted flow
                with pytest.raises(InvalidFlowStateError) as exc_info:
                    await crewai_flow_service.resume_flow(
                        flow_id=deleted_flow.flow_id,
                        resume_context={'client_account_id': '12345'}
                    )
                
                # Verify the error message contains expected information
                assert "deleted" in str(exc_info.value)
                assert "resuming" in str(exc_info.value)
                assert "transition" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_resume_cancelled_flow_raises_invalid_flow_state_error(
        self, crewai_flow_service, mock_discovery_flow_service, cancelled_flow
    ):
        """Test that attempting to resume a cancelled flow raises InvalidFlowStateError"""
        
        # Mock the discovery service to return the cancelled flow
        mock_discovery_flow_service.get_flow_by_id.return_value = cancelled_flow
        
        # Mock the _get_discovery_flow_service method
        with patch.object(crewai_flow_service, '_get_discovery_flow_service', return_value=mock_discovery_flow_service):
            with patch('app.services.crewai_flow_service.CREWAI_FLOWS_AVAILABLE', True):
                # Attempt to resume the cancelled flow
                with pytest.raises(InvalidFlowStateError) as exc_info:
                    await crewai_flow_service.resume_flow(
                        flow_id=cancelled_flow.flow_id,
                        resume_context={'client_account_id': '12345'}
                    )
                
                # Verify the error message contains expected information
                assert "cancelled" in str(exc_info.value)
                assert "resuming" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_resume_flow_validates_terminal_statuses(
        self, crewai_flow_service, mock_discovery_flow_service
    ):
        """Test that all terminal statuses are properly validated"""
        
        terminal_statuses = ['deleted', 'cancelled', 'completed', 'failed']
        
        for status in terminal_statuses:
            # Create flow with terminal status
            flow = MagicMock(spec=DiscoveryFlow)
            flow.flow_id = f"test-{status}-flow-id"
            flow.status = status
            flow.current_phase = "test_phase"
            flow.data_import_id = None
            
            # Mock the discovery service to return the flow
            mock_discovery_flow_service.get_flow_by_id.return_value = flow
            
            # Mock the _get_discovery_flow_service method
            with patch.object(crewai_flow_service, '_get_discovery_flow_service', return_value=mock_discovery_flow_service):
                with patch('app.services.crewai_flow_service.CREWAI_FLOWS_AVAILABLE', True):
                    # Attempt to resume the flow with terminal status
                    with pytest.raises(InvalidFlowStateError) as exc_info:
                        await crewai_flow_service.resume_flow(
                            flow_id=flow.flow_id,
                            resume_context={'client_account_id': '12345'}
                        )
                    
                    # Verify the error message mentions the specific status
                    assert status in str(exc_info.value)

    @pytest.mark.asyncio 
    async def test_resume_flow_non_terminal_status_passes_validation(
        self, crewai_flow_service, mock_discovery_flow_service
    ):
        """Test that non-terminal statuses pass validation (even if they fail later)"""
        
        # Create flow with valid resumable status
        flow = MagicMock(spec=DiscoveryFlow)
        flow.flow_id = "test-valid-flow-id"
        flow.status = "waiting_for_approval"  # Valid resumable status
        flow.current_phase = "field_mapping"
        flow.data_import_id = None
        
        # Mock the discovery service to return the valid flow
        mock_discovery_flow_service.get_flow_by_id.return_value = flow
        
        # Mock the _get_discovery_flow_service method
        with patch.object(crewai_flow_service, '_get_discovery_flow_service', return_value=mock_discovery_flow_service):
            with patch('app.services.crewai_flow_service.CREWAI_FLOWS_AVAILABLE', True):
                with patch('app.core.database.AsyncSessionLocal'):
                    with patch('app.services.master_flow_orchestrator.MasterFlowOrchestrator'):
                        with patch('app.services.crewai_flow_service.UnifiedDiscoveryFlow'):
                            try:
                                # This should NOT raise InvalidFlowStateError for terminal status
                                # (it may raise other errors due to mocking, but not the terminal status error)
                                await crewai_flow_service.resume_flow(
                                    flow_id=flow.flow_id,
                                    resume_context={'client_account_id': '12345'}
                                )
                            except InvalidFlowStateError as e:
                                # If it's a terminal status error, fail the test
                                if "transition from" in str(e) and ("deleted" in str(e) or "cancelled" in str(e) or "completed" in str(e) or "failed" in str(e)):
                                    pytest.fail(f"Should not raise terminal status error for '{flow.status}' status")
                                # Other InvalidFlowStateErrors are expected due to mocking
                            except Exception:
                                # Other exceptions are expected due to incomplete mocking
                                pass