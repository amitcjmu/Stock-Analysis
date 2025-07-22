"""
Unit tests for AssessmentFlowRepository with database operations

This module tests the repository layer for assessment flow data persistence
and multi-tenant isolation.
"""

from datetime import datetime, timezone
from typing import List
from uuid import uuid4

import pytest

try:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.assessment_flow import AssessmentFlowState, AssessmentPhase
    from app.repositories.assessment_flow_repository import AssessmentFlowRepository
    REPOSITORY_AVAILABLE = True
except ImportError:
    # Mock classes for when components don't exist yet
    REPOSITORY_AVAILABLE = False
    
    class AssessmentFlowRepository:
        def __init__(self, db_session, client_account_id):
            self.db_session = db_session
            self.client_account_id = client_account_id
    
    class AssessmentFlowState:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class AssessmentPhase:
        ARCHITECTURE_MINIMUMS = "architecture_minimums"
        TECH_DEBT_ANALYSIS = "tech_debt_analysis"
    
    AsyncSession = object

from tests.fixtures.assessment_fixtures import (
    assert_multi_tenant_isolation,
    async_db_session,
    sample_applications,
    sample_architecture_standards,
    sample_assessment_flow_state,
)


class TestAssessmentFlowRepository:
    """Unit tests for AssessmentFlowRepository with database operations"""
    
    @pytest.fixture
    async def assessment_repository(self, async_db_session):
        """Assessment repository with test database"""
        if not REPOSITORY_AVAILABLE:
            pytest.skip("Repository components not available")
        return AssessmentFlowRepository(async_db_session, client_account_id=1)
    
    @pytest.mark.asyncio
    async def test_create_assessment_flow(
        self,
        assessment_repository,
        sample_applications
    ):
        """Test assessment flow creation with proper data persistence"""
        
        flow_id = await assessment_repository.create_assessment_flow(
            engagement_id=1,
            selected_application_ids=sample_applications,
            created_by="test@example.com"
        )
        
        assert flow_id is not None
        assert isinstance(flow_id, str)
        
        # Verify flow was created in database
        flow_state = await assessment_repository.get_assessment_flow_state(flow_id)
        assert flow_state is not None
        assert flow_state.engagement_id == 1
        assert flow_state.selected_application_ids == sample_applications
    
    @pytest.mark.asyncio
    async def test_save_and_retrieve_flow_state(
        self,
        assessment_repository,
        sample_assessment_flow_state
    ):
        """Test complete flow state persistence and retrieval"""
        
        # Create flow state object
        flow_state = AssessmentFlowState(**sample_assessment_flow_state)
        
        # Save flow state
        await assessment_repository.save_flow_state(flow_state)
        
        # Retrieve and verify
        retrieved_state = await assessment_repository.get_assessment_flow_state(
            flow_state.flow_id
        )
        
        assert retrieved_state is not None
        assert retrieved_state.flow_id == flow_state.flow_id
        assert retrieved_state.status == flow_state.status
        assert retrieved_state.current_phase == flow_state.current_phase
        assert retrieved_state.progress == flow_state.progress
    
    @pytest.mark.asyncio
    async def test_update_flow_state_progress(
        self,
        assessment_repository,
        sample_assessment_flow_state
    ):
        """Test updating flow state progress and phase"""
        
        flow_state = AssessmentFlowState(**sample_assessment_flow_state)
        
        # Save initial state
        await assessment_repository.save_flow_state(flow_state)
        
        # Update state
        flow_state.current_phase = AssessmentPhase.TECH_DEBT_ANALYSIS
        flow_state.progress = 50
        flow_state.status = "processing"
        
        # Save updated state
        await assessment_repository.save_flow_state(flow_state)
        
        # Retrieve and verify updates
        updated_state = await assessment_repository.get_assessment_flow_state(flow_state.flow_id)
        assert updated_state.current_phase == AssessmentPhase.TECH_DEBT_ANALYSIS
        assert updated_state.progress == 50
        assert updated_state.status == "processing"
    
    @pytest.mark.asyncio
    async def test_save_engagement_architecture_standards(
        self,
        assessment_repository,
        sample_architecture_standards
    ):
        """Test saving and retrieving engagement architecture standards"""
        
        engagement_id = 1
        
        # Save standards
        await assessment_repository.save_engagement_architecture_standards(
            engagement_id, sample_architecture_standards
        )
        
        # Retrieve standards
        retrieved_standards = await assessment_repository.get_engagement_architecture_standards(
            engagement_id
        )
        
        assert len(retrieved_standards) == len(sample_architecture_standards)
        
        # Verify specific standard
        java_standard = next(
            (s for s in retrieved_standards if s["requirement_type"] == "java_versions"), 
            None
        )
        assert java_standard is not None
        assert java_standard["mandatory"] is True
        assert java_standard["supported_versions"]["java"] == "11+"
    
    @pytest.mark.asyncio
    async def test_save_application_components(
        self,
        assessment_repository
    ):
        """Test saving and retrieving application component analysis"""
        
        flow_id = "test-flow-123"
        application_id = "app-1"
        
        component_data = {
            "components": [
                {
                    "name": "frontend",
                    "type": "ui",
                    "technology_stack": {"react": "16.14.0"},
                    "complexity_score": 6.5
                }
            ],
            "overall_score": 6.5,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Save component data
        await assessment_repository.save_application_components(
            flow_id, application_id, component_data
        )
        
        # Retrieve component data
        retrieved_data = await assessment_repository.get_application_components(
            flow_id, application_id
        )
        
        assert retrieved_data is not None
        assert len(retrieved_data["components"]) == 1
        assert retrieved_data["components"][0]["name"] == "frontend"
        assert retrieved_data["overall_score"] == 6.5
    
    @pytest.mark.asyncio
    async def test_save_tech_debt_analysis(
        self,
        assessment_repository
    ):
        """Test saving and retrieving tech debt analysis results"""
        
        flow_id = "test-flow-123"
        application_id = "app-1"
        
        tech_debt_data = {
            "overall_tech_debt_score": 7.2,
            "tech_debt_items": [
                {
                    "category": "version_obsolescence",
                    "severity": "high",
                    "description": "Java 8 is end-of-life",
                    "score": 8.5,
                    "component": "backend_api"
                }
            ],
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Save tech debt data
        await assessment_repository.save_tech_debt_analysis(
            flow_id, application_id, tech_debt_data
        )
        
        # Retrieve tech debt data
        retrieved_data = await assessment_repository.get_tech_debt_analysis(
            flow_id, application_id
        )
        
        assert retrieved_data is not None
        assert retrieved_data["overall_tech_debt_score"] == 7.2
        assert len(retrieved_data["tech_debt_items"]) == 1
        assert retrieved_data["tech_debt_items"][0]["severity"] == "high"
    
    @pytest.mark.asyncio
    async def test_save_sixr_decisions(
        self,
        assessment_repository
    ):
        """Test saving and retrieving 6R strategy decisions"""
        
        flow_id = "test-flow-123"
        application_id = "app-1"
        
        sixr_data = {
            "application_name": "Frontend Portal",
            "overall_strategy": "refactor",
            "confidence_score": 0.85,
            "component_treatments": [
                {
                    "component_name": "frontend",
                    "recommended_strategy": "refactor",
                    "rationale": "React upgrade needed"
                }
            ],
            "decision_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Save 6R decisions
        await assessment_repository.save_sixr_decisions(
            flow_id, application_id, sixr_data
        )
        
        # Retrieve 6R decisions
        retrieved_data = await assessment_repository.get_sixr_decisions(
            flow_id, application_id
        )
        
        assert retrieved_data is not None
        assert retrieved_data["overall_strategy"] == "refactor"
        assert retrieved_data["confidence_score"] == 0.85
        assert len(retrieved_data["component_treatments"]) == 1
    
    @pytest.mark.asyncio
    async def test_save_user_input(
        self,
        assessment_repository
    ):
        """Test saving and retrieving user input for flow phases"""
        
        flow_id = "test-flow-123"
        phase = AssessmentPhase.ARCHITECTURE_MINIMUMS
        
        user_input = {
            "architecture_standards": [
                {
                    "requirement_type": "custom_standard",
                    "description": "Custom requirement",
                    "mandatory": False
                }
            ],
            "application_overrides": {
                "app-1": {
                    "override_reason": "Legacy system exception",
                    "approved_by": "architect@example.com"
                }
            }
        }
        
        # Save user input
        await assessment_repository.save_user_input(flow_id, phase, user_input)
        
        # Retrieve user input
        retrieved_input = await assessment_repository.get_user_input(flow_id, phase)
        
        assert retrieved_input is not None
        assert "architecture_standards" in retrieved_input
        assert "application_overrides" in retrieved_input
        assert len(retrieved_input["architecture_standards"]) == 1
        assert "app-1" in retrieved_input["application_overrides"]
    
    @pytest.mark.asyncio
    async def test_multi_tenant_data_isolation(
        self,
        async_db_session: AsyncSession
    ):
        """Test that repository enforces multi-tenant data isolation"""
        
        if not REPOSITORY_AVAILABLE:
            pytest.skip("Repository components not available")
        
        # Create repositories for different clients
        repo_1 = AssessmentFlowRepository(async_db_session, client_account_id=1)
        repo_2 = AssessmentFlowRepository(async_db_session, client_account_id=2)
        
        # Create flow for client 1
        flow_id_1 = await repo_1.create_assessment_flow(
            engagement_id=1,
            selected_application_ids=["app-1"],
            created_by="client1@example.com"
        )
        
        # Try to access from client 2 (should fail/return None)
        flow_state_2 = await repo_2.get_assessment_flow_state(flow_id_1)
        assert flow_state_2 is None
        
        # Client 1 should still have access
        flow_state_1 = await repo_1.get_assessment_flow_state(flow_id_1)
        assert flow_state_1 is not None
        assert flow_state_1.client_account_id == 1
    
    @pytest.mark.asyncio
    async def test_engagement_isolation(
        self,
        async_db_session: AsyncSession
    ):
        """Test that flows are isolated by engagement"""
        
        if not REPOSITORY_AVAILABLE:
            pytest.skip("Repository components not available")
        
        repo = AssessmentFlowRepository(async_db_session, client_account_id=1)
        
        # Create flows for different engagements
        flow_id_eng1 = await repo.create_assessment_flow(
            engagement_id=1,
            selected_application_ids=["app-1"],
            created_by="user@example.com"
        )
        
        flow_id_eng2 = await repo.create_assessment_flow(
            engagement_id=2,
            selected_application_ids=["app-2"],
            created_by="user@example.com"
        )
        
        # Get flows by engagement
        flows_eng1 = await repo.get_flows_by_engagement(engagement_id=1)
        flows_eng2 = await repo.get_flows_by_engagement(engagement_id=2)
        
        # Verify isolation
        assert len(flows_eng1) == 1
        assert len(flows_eng2) == 1
        assert flows_eng1[0].flow_id == flow_id_eng1
        assert flows_eng2[0].flow_id == flow_id_eng2
    
    @pytest.mark.asyncio
    async def test_flow_deletion_and_cleanup(
        self,
        assessment_repository,
        sample_assessment_flow_state
    ):
        """Test flow deletion and associated data cleanup"""
        
        flow_state = AssessmentFlowState(**sample_assessment_flow_state)
        
        # Save flow and associated data
        await assessment_repository.save_flow_state(flow_state)
        await assessment_repository.save_application_components(
            flow_state.flow_id, 
            "app-1", 
            {"components": [{"name": "test"}]}
        )
        
        # Verify data exists
        retrieved_state = await assessment_repository.get_assessment_flow_state(flow_state.flow_id)
        assert retrieved_state is not None
        
        # Delete flow
        await assessment_repository.delete_assessment_flow(flow_state.flow_id)
        
        # Verify data is cleaned up
        deleted_state = await assessment_repository.get_assessment_flow_state(flow_state.flow_id)
        assert deleted_state is None
        
        # Verify associated data is also cleaned up
        components = await assessment_repository.get_application_components(flow_state.flow_id, "app-1")
        assert components is None
    
    @pytest.mark.asyncio
    async def test_repository_error_handling(
        self,
        assessment_repository
    ):
        """Test repository error handling for invalid operations"""
        
        # Test getting non-existent flow
        flow_state = await assessment_repository.get_assessment_flow_state("non-existent-flow")
        assert flow_state is None
        
        # Test saving data for non-existent flow
        with pytest.raises((ValueError, Exception)):
            await assessment_repository.save_application_components(
                "non-existent-flow",
                "app-1",
                {"components": []}
            )
    
    @pytest.mark.asyncio
    async def test_concurrent_flow_operations(
        self,
        assessment_repository,
        sample_assessment_flow_state
    ):
        """Test concurrent operations on the same flow"""
        
        flow_state = AssessmentFlowState(**sample_assessment_flow_state)
        
        # Save initial state
        await assessment_repository.save_flow_state(flow_state)
        
        # Simulate concurrent updates
        flow_state_1 = flow_state
        flow_state_1.progress = 30
        
        flow_state_2 = flow_state
        flow_state_2.progress = 40
        
        # Save both concurrently
        import asyncio
        await asyncio.gather(
            assessment_repository.save_flow_state(flow_state_1),
            assessment_repository.save_flow_state(flow_state_2)
        )
        
        # Verify final state (should be one of the concurrent updates)
        final_state = await assessment_repository.get_assessment_flow_state(flow_state.flow_id)
        assert final_state.progress in [30, 40]  # Either update should be valid


class TestRepositoryQueries:
    """Test complex repository queries and reporting"""
    
    @pytest.fixture
    async def assessment_repository(self, async_db_session):
        """Assessment repository with test database"""
        if not REPOSITORY_AVAILABLE:
            pytest.skip("Repository components not available")
        return AssessmentFlowRepository(async_db_session, client_account_id=1)
    
    @pytest.mark.asyncio
    async def test_get_flow_statistics(
        self,
        assessment_repository
    ):
        """Test getting flow statistics for reporting"""
        
        # Create multiple flows in different states
        flow_ids = []
        for i in range(3):
            flow_id = await assessment_repository.create_assessment_flow(
                engagement_id=1,
                selected_application_ids=[f"app-{i}"],
                created_by="test@example.com"
            )
            flow_ids.append(flow_id)
        
        # Update flows to different phases
        for i, flow_id in enumerate(flow_ids):
            flow_state = await assessment_repository.get_assessment_flow_state(flow_id)
            flow_state.current_phase = [
                AssessmentPhase.ARCHITECTURE_MINIMUMS,
                AssessmentPhase.TECH_DEBT_ANALYSIS,
                AssessmentPhase.TECH_DEBT_ANALYSIS
            ][i]
            flow_state.status = ["initialized", "processing", "completed"][i]
            await assessment_repository.save_flow_state(flow_state)
        
        # Get statistics
        stats = await assessment_repository.get_flow_statistics(engagement_id=1)
        
        assert stats["total_flows"] == 3
        assert stats["flows_by_status"]["initialized"] == 1
        assert stats["flows_by_status"]["processing"] == 1
        assert stats["flows_by_status"]["completed"] == 1
        assert stats["flows_by_phase"][AssessmentPhase.ARCHITECTURE_MINIMUMS] == 1
        assert stats["flows_by_phase"][AssessmentPhase.TECH_DEBT_ANALYSIS] == 2
    
    @pytest.mark.asyncio
    async def test_search_flows_by_criteria(
        self,
        assessment_repository
    ):
        """Test searching flows by various criteria"""
        
        # Create flows with different characteristics
        flow_id_1 = await assessment_repository.create_assessment_flow(
            engagement_id=1,
            selected_application_ids=["app-1", "app-2"],
            created_by="user1@example.com"
        )
        
        flow_id_2 = await assessment_repository.create_assessment_flow(
            engagement_id=1,
            selected_application_ids=["app-3"],
            created_by="user2@example.com"
        )
        
        # Search by application count
        flows_with_multiple_apps = await assessment_repository.search_flows(
            engagement_id=1,
            min_application_count=2
        )
        assert len(flows_with_multiple_apps) == 1
        assert flows_with_multiple_apps[0].flow_id == flow_id_1
        
        # Search by created_by
        user1_flows = await assessment_repository.search_flows(
            engagement_id=1,
            created_by="user1@example.com"
        )
        assert len(user1_flows) == 1
        assert user1_flows[0].flow_id == flow_id_1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])