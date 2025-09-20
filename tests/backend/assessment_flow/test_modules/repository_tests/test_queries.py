"""
Assessment Flow Repository Query Tests

Tests for complex repository queries, statistics, and search functionality.
Covers reporting and analytics operations for assessment flows.

Generated with CC for MFO compliance.
"""

import pytest

from .common import (
    DEMO_CLIENT_ACCOUNT_ID,
    DEMO_ENGAGEMENT_ID,
    REPOSITORY_AVAILABLE,
    AssessmentFlowRepository,
    AssessmentPhase,
)


class TestRepositoryQueries:
    """Test complex repository queries and reporting - MFO compliant"""

    @pytest.fixture
    async def assessment_repository(self, async_db_session):
        """Assessment repository with test database - MFO compliant"""
        if not REPOSITORY_AVAILABLE:
            pytest.skip("Repository components not available")
        return AssessmentFlowRepository(async_db_session, client_account_id=DEMO_CLIENT_ACCOUNT_ID)

    @pytest.mark.mfo
    @pytest.mark.assessment_flow
    @pytest.mark.database
    @pytest.mark.async_test
    async def test_get_flow_statistics(self, assessment_repository):
        """Test getting flow statistics for reporting - MFO compliant"""

        # Create multiple flows in different states
        flow_ids = []
        for i in range(3):
            flow_id = await assessment_repository.create_assessment_flow(
                engagement_id=DEMO_ENGAGEMENT_ID,
                selected_application_ids=[f"app-{i}"],
                created_by="test@example.com",
            )
            flow_ids.append(flow_id)

        # Update flows to different phases
        for i, flow_id in enumerate(flow_ids):
            flow_state = await assessment_repository.get_assessment_flow_state(flow_id)
            flow_state.current_phase = [
                AssessmentPhase.ARCHITECTURE_MINIMUMS,
                AssessmentPhase.TECH_DEBT_ANALYSIS,
                AssessmentPhase.TECH_DEBT_ANALYSIS,
            ][i]
            flow_state.status = ["initialized", "processing", "completed"][i]
            await assessment_repository.save_flow_state(flow_state)

        # Get statistics
        stats = await assessment_repository.get_flow_statistics(engagement_id=DEMO_ENGAGEMENT_ID)

        assert stats["total_flows"] == 3
        assert stats["flows_by_status"]["initialized"] == 1
        assert stats["flows_by_status"]["processing"] == 1
        assert stats["flows_by_status"]["completed"] == 1
        assert stats["flows_by_phase"][AssessmentPhase.ARCHITECTURE_MINIMUMS] == 1
        assert stats["flows_by_phase"][AssessmentPhase.TECH_DEBT_ANALYSIS] == 2

    @pytest.mark.mfo
    @pytest.mark.assessment_flow
    @pytest.mark.database
    @pytest.mark.async_test
    async def test_search_flows_by_criteria(self, assessment_repository):
        """Test searching flows by various criteria - MFO compliant"""

        # Create flows with different characteristics
        flow_id_1 = await assessment_repository.create_assessment_flow(
            engagement_id=DEMO_ENGAGEMENT_ID,
            selected_application_ids=["app-1", "app-2"],
            created_by="user1@example.com",
        )

        await assessment_repository.create_assessment_flow(
            engagement_id=DEMO_ENGAGEMENT_ID,
            selected_application_ids=["app-3"],
            created_by="user2@example.com",
        )

        # Search by application count
        flows_with_multiple_apps = await assessment_repository.search_flows(
            engagement_id=DEMO_ENGAGEMENT_ID, min_application_count=2
        )
        assert len(flows_with_multiple_apps) == 1
        assert flows_with_multiple_apps[0].flow_id == flow_id_1

        # Search by created_by
        user1_flows = await assessment_repository.search_flows(
            engagement_id=DEMO_ENGAGEMENT_ID, created_by="user1@example.com"
        )
        assert len(user1_flows) == 1
        assert user1_flows[0].flow_id == flow_id_1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
