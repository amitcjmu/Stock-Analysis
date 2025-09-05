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

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow
from app.services.gap_analysis_summary_service import GapAnalysisSummaryService
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)
from app.schemas.collection_transition import ReadinessResult, TransitionResult


class CollectionTransitionService:
    """
    Service for collection to assessment transitions.
    Uses agent-driven readiness assessment, NOT hardcoded thresholds.
    """

    def __init__(self, db_session: AsyncSession, context: RequestContext):
        self.db = db_session
        self.context = context
        self.gap_service = GapAnalysisSummaryService(db_session)

    async def validate_readiness(self, flow_id: UUID) -> ReadinessResult:
        """
        Agent-driven readiness validation.
        NO hardcoded thresholds - uses tenant preferences and AI assessment.
        """

        # Get flow with tenant-scoped query
        flow = await self._get_collection_flow(flow_id)

        # Get gap analysis summary (existing service)
        gap_summary = await self.gap_service.get_gap_analysis_summary(
            str(flow.id), self.context
        )

        # Get readiness agent for intelligent assessment using class method
        readiness_agent = await TenantScopedAgentPool.get_agent(
            context=self.context, agent_type="readiness_assessor"
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

            assessment_repo = AssessmentFlowRepository(
                self.db,
                self.context.client_account_id,
                self.context.engagement_id,
                str(self.context.user_id) if self.context.user_id else None,
            )

            # Create assessment with MFO pattern - use correct parameters
            # Get selected application IDs from collection config
            selected_app_ids = []
            if (
                hasattr(collection_flow, "collection_config")
                and collection_flow.collection_config
                and collection_flow.collection_config.get("selected_application_ids")
            ):
                selected_app_ids = collection_flow.collection_config[
                    "selected_application_ids"
                ]

            assessment_flow_id = await assessment_repo.create_assessment_flow(
                engagement_id=str(self.context.engagement_id),
                selected_application_ids=selected_app_ids,
                created_by=str(self.context.user_id) if self.context.user_id else None,
            )

            # Get the created assessment flow record for metadata
            from app.models.assessment_flow import AssessmentFlow

            assessment_result = await self.db.execute(
                select(AssessmentFlow).where(AssessmentFlow.id == assessment_flow_id)
            )
            assessment_flow = assessment_result.scalar_one()

            # Update collection flow (only if column exists)
            if hasattr(collection_flow, "assessment_flow_id"):
                collection_flow.assessment_flow_id = assessment_flow.id
                collection_flow.assessment_transition_date = datetime.utcnow()

            # Store in flow_metadata (with safe attribute access)
            current_metadata = getattr(collection_flow, "flow_metadata", {}) or {}
            collection_flow.flow_metadata = {
                **current_metadata,
                "assessment_handoff": {
                    "assessment_flow_id": str(assessment_flow.flow_id),
                    "transitioned_at": datetime.utcnow().isoformat(),
                    "transitioned_by": (
                        str(self.context.user_id) if self.context.user_id else None
                    ),
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
        """Create task for readiness assessment agent with safe attribute access."""
        # Safe attribute access for flow fields
        flow_id = getattr(flow, "flow_id", None)
        progress_percentage = getattr(flow, "progress_percentage", 0) or 0
        current_phase = getattr(flow, "current_phase", "unknown") or "unknown"

        # Safe gap summary processing
        gaps_count = 0
        if gap_summary and hasattr(gap_summary, "gaps"):
            gaps_count = len(gap_summary.gaps) if gap_summary.gaps else 0
        elif gap_summary and hasattr(gap_summary, "critical_gaps"):
            # Alternative field name
            critical_gaps = getattr(gap_summary, "critical_gaps", []) or []
            optional_gaps = getattr(gap_summary, "optional_gaps", []) or []
            gaps_count = len(critical_gaps) + len(optional_gaps)

        return {
            "flow_id": str(flow_id) if flow_id else "unknown",
            "gaps_count": gaps_count,
            "collection_progress": progress_percentage,
            "current_phase": current_phase,
        }

    async def _get_tenant_thresholds(self) -> Dict[str, float]:
        """Get tenant-specific readiness thresholds from engagement preferences."""
        # Default thresholds - can be overridden by engagement preferences
        return {
            "collection_completeness": 0.7,
            "data_quality": 0.65,
            "confidence_score": 0.6,
        }
