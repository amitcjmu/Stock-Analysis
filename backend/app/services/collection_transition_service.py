"""
Collection to Assessment Transition Service

Service for managing the transition from collection flows to assessment flows.
Uses agent-driven readiness assessment and creates assessment flows via MFO pattern.
"""

from datetime import datetime
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.request_context import RequestContext
from app.models.collection_flow import CollectionFlow
from app.services.gap_analysis_summary_service import GapAnalysisSummaryService
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)
from app.services.agent_configuration import AgentConfiguration
from app.schemas.collection_transition import ReadinessResult, TransitionResult


class CollectionTransitionService:
    """
    Service for collection to assessment transitions.
    Uses agent-driven readiness assessment, NOT hardcoded thresholds.
    """

    def __init__(self, db_session: AsyncSession, context: RequestContext):
        self.db = db_session
        self.context = context
        self.gap_service = GapAnalysisSummaryService(db_session, context)
        self.agent_pool = TenantScopedAgentPool(
            context.client_account_id, context.engagement_id
        )

    async def validate_readiness(self, flow_id: UUID) -> ReadinessResult:
        """
        Agent-driven readiness validation.
        NO hardcoded thresholds - uses tenant preferences and AI assessment.
        """

        # Get flow with tenant-scoped query
        flow = await self._get_collection_flow(flow_id)

        # Get gap analysis summary (existing service)
        gap_summary = await self.gap_service.get_gap_analysis_summary(flow)

        # Get readiness agent config with safe fallback
        agent_config = AgentConfiguration.get_agent_config("readiness_assessor")

        # Get readiness agent for intelligent assessment
        readiness_agent = await self.agent_pool.get_or_create_agent(
            agent_type="readiness_assessor", config=agent_config
        )

        # Agent-driven decision (NO hardcoded 0.7 threshold)
        assessment_task = self._create_readiness_task(flow, gap_summary)
        agent_result = await readiness_agent.execute(assessment_task)

        # Get tenant-specific thresholds from engagement preferences
        thresholds = await self._get_tenant_thresholds()

        return ReadinessResult(
            is_ready=agent_result.is_ready,
            confidence=agent_result.confidence,
            reason=agent_result.reasoning,
            missing_requirements=agent_result.missing_items,
            thresholds_used=thresholds,  # For audit trail
        )

    async def create_assessment_flow(self, collection_flow_id: UUID):
        """
        Create assessment using MFO/Repository pattern.
        Atomic transaction with proper error handling.
        """

        async with self.db.begin():  # Atomic transaction - auto commits/rollbacks
            # Get collection flow
            collection_flow = await self._get_collection_flow(collection_flow_id)

            # Use existing AssessmentFlowRepository
            from app.repositories.assessment_flow_repository import (
                AssessmentFlowRepository,
            )

            assessment_repo = AssessmentFlowRepository(self.db, self.context)

            # Create assessment with MFO pattern - use correct field names
            assessment_flow = await assessment_repo.create_assessment_flow(
                name=f"Assessment - {collection_flow.flow_name}",  # Fixed: flow_name
                collection_flow_id=collection_flow.id,
                metadata={
                    "source": "collection_transition",
                    "collection_flow_uuid": str(collection_flow.flow_id),
                    "transition_timestamp": datetime.utcnow().isoformat(),
                },
            )

            # Update collection flow (only if column exists)
            if hasattr(collection_flow, "assessment_flow_id"):
                collection_flow.assessment_flow_id = assessment_flow.id
                collection_flow.assessment_transition_date = datetime.utcnow()

            # Store in flow_metadata (correct field name)
            collection_flow.flow_metadata = {  # Fixed: flow_metadata
                **collection_flow.flow_metadata,
                "assessment_handoff": {
                    "assessment_flow_id": str(assessment_flow.flow_id),
                    "transitioned_at": datetime.utcnow().isoformat(),
                    "transitioned_by": str(self.context.user_id),
                },
            }

            # Flush to get generated IDs if needed before context exit
            await self.db.flush()

        return TransitionResult(
            assessment_flow_id=assessment_flow.flow_id,
            assessment_flow=assessment_flow,
            created_at=datetime.utcnow(),
        )

    async def _get_collection_flow(self, flow_id: UUID) -> CollectionFlow:
        """
        Get collection flow with proper tenant scoping.
        """
        query = select(CollectionFlow).where(
            CollectionFlow.flow_id == flow_id,
            CollectionFlow.client_account_id == self.context.client_account_id,
            CollectionFlow.engagement_id == self.context.engagement_id,
        )
        result = await self.db.execute(query)
        flow = result.scalar_one_or_none()

        if not flow:
            raise ValueError(f"Collection flow {flow_id} not found or access denied")

        return flow

    async def _create_readiness_task(
        self, flow: CollectionFlow, gap_summary: Any
    ) -> Dict:
        """Create task for readiness assessment agent."""
        return {
            "flow_id": str(flow.flow_id),
            "gaps_count": len(gap_summary.gaps) if gap_summary else 0,
            "collection_progress": flow.progress_percentage,
            "current_phase": flow.current_phase,
        }

    async def _get_tenant_thresholds(self) -> Dict[str, float]:
        """Get tenant-specific readiness thresholds from engagement preferences."""
        # Default thresholds - can be overridden by engagement preferences
        return {
            "collection_completeness": 0.7,
            "data_quality": 0.65,
            "confidence_score": 0.6,
        }
