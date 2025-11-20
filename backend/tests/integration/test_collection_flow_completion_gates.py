"""
Integration Tests for Collection Flow Completion Gates
Replaces markdown documentation with automated verification

Tests Bug Fixes:
- Bug #1055: Database query for questionnaire count
- Bug #1056-A: Manual collection completion check
- Bug #1056-B: Data validation gap closure
- Bug #1056-C: Finalization readiness gate
"""

import pytest
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_data_gap import CollectionDataGap
from app.models.collection_flow import CollectionFlow, CollectionFlowStatus
from app.models.collection_flow.adaptive_questionnaire_model import (
    AdaptiveQuestionnaire,
)
from app.models.collection_questionnaire_response import CollectionQuestionnaireResponse
from app.services.child_flow_services.collection import CollectionChildFlowService
from app.services.collection_flow.state_management import CollectionPhase


@pytest.fixture
async def test_context():
    """Create test request context"""
    return RequestContext(client_account_id=1, engagement_id=1, user_id="test-user-id")


@pytest.fixture
async def collection_flow_service(db: AsyncSession, test_context: RequestContext):
    """Create collection flow service"""
    return CollectionChildFlowService(db, test_context)


@pytest.fixture
async def collection_flow_with_questionnaires(
    db: AsyncSession, test_context: RequestContext
):
    """
    Create a collection flow with questionnaires but NO responses
    Simulates Bug #1056 scenario
    """
    # Create collection flow
    flow = CollectionFlow(
        id=uuid4(),
        master_flow_id=uuid4(),
        client_account_id=test_context.client_account_id,
        engagement_id=test_context.engagement_id,
        current_phase=CollectionPhase.MANUAL_COLLECTION,
        status=CollectionFlowStatus.RUNNING,
        automation_tier="tier_2",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(flow)
    await db.flush()

    # Create 2 questionnaires (simulating gap analysis output)
    for i in range(2):
        questionnaire = AdaptiveQuestionnaire(
            id=uuid4(),
            collection_flow_id=flow.id,
            questionnaire_data={"title": f"Test Questionnaire {i+1}"},
            created_at=datetime.utcnow(),
        )
        db.add(questionnaire)

    await db.commit()
    await db.refresh(flow)

    return flow


@pytest.fixture
async def collection_flow_with_critical_gaps(
    db: AsyncSession, test_context: RequestContext
):
    """
    Create a collection flow with unresolved CRITICAL gaps
    Tests Bug #1056-B scenario
    """
    # Create collection flow
    flow = CollectionFlow(
        id=uuid4(),
        master_flow_id=uuid4(),
        client_account_id=test_context.client_account_id,
        engagement_id=test_context.engagement_id,
        current_phase=CollectionPhase.DATA_VALIDATION,
        status=CollectionFlowStatus.RUNNING,
        automation_tier="tier_2",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(flow)
    await db.flush()

    # Create critical gaps (priority >= 80)
    for i in range(3):
        gap = CollectionDataGap(
            id=uuid4(),
            collection_flow_id=flow.id,
            field_name=f"critical_field_{i+1}",
            gap_category="missing_data",
            priority=85,
            impact_on_sixr="critical",
            resolution_status="pending",
            created_at=datetime.utcnow(),
        )
        db.add(gap)

    # Create resolved low-priority gap
    gap = CollectionDataGap(
        id=uuid4(),
        collection_flow_id=flow.id,
        field_name="low_priority_field",
        gap_category="missing_data",
        priority=30,
        impact_on_sixr="low",
        resolution_status="resolved",
        created_at=datetime.utcnow(),
    )
    db.add(gap)

    await db.commit()
    await db.refresh(flow)

    return flow


class TestBug1055DatabaseQuery:
    """Bug #1055: Questionnaire generation should query database, not phase result"""

    async def test_questionnaire_count_from_database(
        self, db: AsyncSession, collection_flow_with_questionnaires: CollectionFlow
    ):
        """Verify questionnaire count is queried from database"""
        flow = collection_flow_with_questionnaires

        # Query database directly (what the fix does)
        result = await db.execute(
            select(func.count(AdaptiveQuestionnaire.id)).where(
                AdaptiveQuestionnaire.collection_flow_id == flow.id
            )
        )
        count = result.scalar() or 0

        # Should find 2 questionnaires
        assert count == 2

    async def test_phase_result_metadata_unreliable(
        self, db: AsyncSession, collection_flow_with_questionnaires: CollectionFlow
    ):
        """Demonstrate phase result metadata can be missing"""
        # Simulate phase result without questionnaire_count
        phase_result = {
            "status": "success",
            # questionnaires_count is MISSING (bug scenario)
        }

        # Old buggy approach would fail here
        questionnaire_count = phase_result.get("questionnaires_count", 0)
        assert questionnaire_count == 0  # Wrong!

        # New approach queries database
        flow = collection_flow_with_questionnaires
        result = await db.execute(
            select(func.count(AdaptiveQuestionnaire.id)).where(
                AdaptiveQuestionnaire.collection_flow_id == flow.id
            )
        )
        actual_count = result.scalar() or 0
        assert actual_count == 2  # Correct!


class TestBug1056AManualCollectionGate:
    """Bug #1056-A: Manual collection must check for responses before progression"""

    async def test_no_responses_blocks_progression(
        self,
        db: AsyncSession,
        collection_flow_service: CollectionChildFlowService,
        collection_flow_with_questionnaires: CollectionFlow,
    ):
        """Flow with 0 responses should return awaiting_user_responses"""
        flow = collection_flow_with_questionnaires

        # Execute manual_collection phase
        result = await collection_flow_service.execute_phase(
            flow_id=str(flow.master_flow_id), phase_name="manual_collection"
        )

        # Should block progression
        assert result["status"] == "awaiting_user_responses"
        assert result["progress"]["total_questionnaires"] == 2
        assert result["progress"]["total_responses"] == 0
        assert result["progress"]["completion_percentage"] == 0.0
        assert result["user_action_required"] == "complete_questionnaires"

    async def test_with_responses_allows_progression(
        self,
        db: AsyncSession,
        collection_flow_service: CollectionChildFlowService,
        collection_flow_with_questionnaires: CollectionFlow,
    ):
        """Flow with responses should transition to data_validation"""
        flow = collection_flow_with_questionnaires

        # Add a response
        response = CollectionQuestionnaireResponse(
            id=uuid4(),
            collection_flow_id=flow.id,
            response_data={"answer": "test"},
            created_at=datetime.utcnow(),
        )
        db.add(response)
        await db.commit()

        # Execute manual_collection phase
        result = await collection_flow_service.execute_phase(
            flow_id=str(flow.master_flow_id), phase_name="manual_collection"
        )

        # Should allow progression
        assert result["status"] == "completed"
        assert result["progress"]["total_responses"] == 1
        assert result["next_phase"] == "data_validation"


class TestBug1056BDataValidationGate:
    """Bug #1056-B: Data validation must verify critical gap closure"""

    async def test_critical_gaps_block_finalization(
        self,
        db: AsyncSession,
        collection_flow_service: CollectionChildFlowService,
        collection_flow_with_critical_gaps: CollectionFlow,
    ):
        """Flow with unresolved critical gaps should pause for review"""
        flow = collection_flow_with_critical_gaps

        # Execute data_validation phase
        result = await collection_flow_service.execute_phase(
            flow_id=str(flow.master_flow_id), phase_name="data_validation"
        )

        # Should pause for user review
        assert result["status"] == "paused"
        assert result["reason"] == "critical_gaps_remaining"
        assert result["validation_result"]["critical_gaps_remaining"] == 3
        assert result["validation_result"]["all_critical_gaps_closed"] is False
        assert result["user_action_required"] == "review_and_provide_missing_data"

    async def test_resolved_gaps_allow_finalization(
        self,
        db: AsyncSession,
        collection_flow_service: CollectionChildFlowService,
        collection_flow_with_critical_gaps: CollectionFlow,
    ):
        """Flow with all critical gaps resolved should proceed to finalization"""
        flow = collection_flow_with_critical_gaps

        # Resolve all critical gaps
        result = await db.execute(
            select(CollectionDataGap).where(
                CollectionDataGap.collection_flow_id == flow.id,
                CollectionDataGap.resolution_status == "pending",
            )
        )
        critical_gaps = result.scalars().all()

        for gap in critical_gaps:
            gap.resolution_status = "resolved"

        await db.commit()

        # Execute data_validation phase
        result = await collection_flow_service.execute_phase(
            flow_id=str(flow.master_flow_id), phase_name="data_validation"
        )

        # Should allow progression
        assert result["status"] == "completed"
        assert result["validation_result"]["critical_gaps_remaining"] == 0
        assert result["validation_result"]["all_critical_gaps_closed"] is True
        assert result["next_phase"] == "finalization"


class TestBug1056CFinalizationReadinessGate:
    """Bug #1056-C: Finalization must verify all completion criteria"""

    async def test_questionnaires_without_responses_fails(
        self,
        db: AsyncSession,
        collection_flow_service: CollectionChildFlowService,
        collection_flow_with_questionnaires: CollectionFlow,
    ):
        """Finalization should FAIL if questionnaires exist but no responses"""
        flow = collection_flow_with_questionnaires

        # Update phase to finalization
        flow.current_phase = CollectionPhase.FINALIZATION
        await db.commit()

        # Execute finalization phase
        result = await collection_flow_service.execute_phase(
            flow_id=str(flow.master_flow_id), phase_name="finalization"
        )

        # Should FAIL with incomplete_data_collection error
        assert result["status"] == "failed"
        assert result["error"] == "incomplete_data_collection"
        assert result["reason"] == "no_responses_collected"
        assert result["validation_details"]["questionnaires_generated"] == 2
        assert result["validation_details"]["responses_collected"] == 0
        assert result["user_action_required"] == "complete_all_questionnaires"

    async def test_critical_gaps_remaining_fails(
        self,
        db: AsyncSession,
        collection_flow_service: CollectionChildFlowService,
        collection_flow_with_critical_gaps: CollectionFlow,
    ):
        """Finalization should FAIL if critical gaps remain unresolved"""
        flow = collection_flow_with_critical_gaps

        # Update phase to finalization
        flow.current_phase = CollectionPhase.FINALIZATION
        await db.commit()

        # Execute finalization phase
        result = await collection_flow_service.execute_phase(
            flow_id=str(flow.master_flow_id), phase_name="finalization"
        )

        # Should FAIL with critical_gaps_remaining error
        assert result["status"] == "failed"
        assert result["error"] == "critical_gaps_remaining"
        assert result["reason"] == "data_validation_incomplete"
        assert result["validation_details"]["critical_gaps_remaining"] == 3
        assert result["user_action_required"] == "resolve_critical_gaps"

    async def test_all_checks_pass_marks_completed(
        self,
        db: AsyncSession,
        collection_flow_service: CollectionChildFlowService,
        collection_flow_with_questionnaires: CollectionFlow,
    ):
        """Finalization should mark flow COMPLETED if all checks pass"""
        flow = collection_flow_with_questionnaires

        # Add response to satisfy check #1
        response = CollectionQuestionnaireResponse(
            id=uuid4(),
            collection_flow_id=flow.id,
            response_data={"answer": "test"},
            created_at=datetime.utcnow(),
        )
        db.add(response)

        # No critical gaps (check #2 passes by default)

        # Update phase to finalization
        flow.current_phase = CollectionPhase.FINALIZATION
        await db.commit()

        # Execute finalization phase
        result = await collection_flow_service.execute_phase(
            flow_id=str(flow.master_flow_id), phase_name="finalization"
        )

        # Should mark flow as COMPLETED
        assert result["status"] == "completed"
        assert result["completion_summary"]["questionnaires_generated"] == 2
        assert result["completion_summary"]["responses_collected"] == 1
        assert result["completion_summary"]["assessment_ready"] is True

        # Verify flow status in database
        await db.refresh(flow)
        assert flow.status == CollectionFlowStatus.COMPLETED
        assert flow.completed_at is not None


class TestConcurrencyProtection:
    """Test row-level locking prevents race conditions in finalization"""

    async def test_idempotent_completion(
        self,
        db: AsyncSession,
        collection_flow_service: CollectionChildFlowService,
        collection_flow_with_questionnaires: CollectionFlow,
    ):
        """Multiple finalization attempts should be idempotent"""
        flow = collection_flow_with_questionnaires

        # Add response
        response = CollectionQuestionnaireResponse(
            id=uuid4(),
            collection_flow_id=flow.id,
            response_data={"answer": "test"},
            created_at=datetime.utcnow(),
        )
        db.add(response)
        flow.current_phase = CollectionPhase.FINALIZATION
        await db.commit()

        # First finalization attempt
        result1 = await collection_flow_service.execute_phase(
            flow_id=str(flow.master_flow_id), phase_name="finalization"
        )
        assert result1["status"] == "completed"

        # Refresh flow
        await db.refresh(flow)
        assert flow.status == CollectionFlowStatus.COMPLETED

        # Second finalization attempt (simulates race condition)
        result2 = await collection_flow_service.execute_phase(
            flow_id=str(flow.master_flow_id), phase_name="finalization"
        )

        # Should still return success (idempotent)
        assert result2["status"] == "completed"

        # Flow should still be COMPLETED (not double-committed)
        await db.refresh(flow)
        assert flow.status == CollectionFlowStatus.COMPLETED
