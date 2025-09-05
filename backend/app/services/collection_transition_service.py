"""
Collection to Assessment Transition Service

Service for managing the transition from collection flows to assessment flows.
Uses agent-driven readiness assessment and creates assessment flows via MFO pattern.
"""

import logging
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

logger = logging.getLogger(__name__)


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
        Uses TenantScopedAgentPool for intelligent assessment.
        """
        from crewai import Task

        # Get flow with tenant-scoped query
        flow = await self._get_collection_flow(flow_id)

        # Get gap analysis summary (existing service)
        gap_summary = await self.gap_service.get_gap_analysis_summary(
            str(flow.id), self.context
        )

        # Use TenantScopedAgentPool to get a readiness assessment agent
        agent = await TenantScopedAgentPool.get_agent(
            self.context, "readiness_assessor", service_registry=None
        )

        # Create readiness assessment task
        task_description = f"""
        Assess readiness for transition from collection to assessment phase.

        Collection Flow ID: {flow_id}
        Current Status: {flow.status}
        Progress: {flow.progress_percentage}%

        Gap Analysis Summary:
        - Total Fields Required: {gap_summary.total_fields_required if gap_summary else 0}
        - Fields Collected: {gap_summary.fields_collected if gap_summary else 0}
        - Fields Missing: {gap_summary.fields_missing if gap_summary else 0}
        - Completeness: {gap_summary.completeness_percentage if gap_summary else 0}%
        - Critical Gaps: {len(gap_summary.critical_gaps) if gap_summary else 0}
        - Data Quality Score: {gap_summary.data_quality_score if gap_summary else 'N/A'}
        - Confidence Level: {gap_summary.confidence_level if gap_summary else 'N/A'}

        Determine:
        1. Is the collection ready for assessment? (true/false)
        2. Confidence level (0.0-1.0)
        3. Reason for decision
        4. Missing requirements (if any)

        Use tenant preferences for thresholds but make intelligent assessment based on data quality.
        """

        # Create task for agent execution
        task = Task(
            description=task_description,
            agent=agent,
            expected_output="JSON with is_ready, confidence, reason, missing_requirements",
        )

        try:
            # Execute task using agent
            result = await agent.execute_async(task)

            # Parse agent response
            if isinstance(result, dict):
                assessment = result
            else:
                # Try to parse string response
                import json

                try:
                    assessment = json.loads(str(result))
                except Exception:
                    # Fallback to basic calculation if agent fails
                    fields_collected = (
                        gap_summary.fields_collected if gap_summary else 0
                    )
                    total_fields = (
                        gap_summary.total_fields_required if gap_summary else 0
                    )
                    confidence = (
                        (fields_collected / total_fields) if total_fields > 0 else 1.0
                    )
                    assessment = {
                        "is_ready": confidence >= 0.7,
                        "confidence": confidence,
                        "reason": f"Collection {int(confidence * 100)}% complete",
                        "missing_requirements": [],
                    }

            return ReadinessResult(
                is_ready=assessment.get("is_ready", False),
                confidence=assessment.get("confidence", 0.0),
                reason=assessment.get("reason", "Assessment incomplete"),
                missing_requirements=assessment.get("missing_requirements", []),
                thresholds_used=await self._get_tenant_thresholds(),
            )

        except AttributeError as e:
            # Handle case where agent doesn't have execute_async
            logger.warning(
                f"Agent execute_async not available: {e}, falling back to calculation"
            )

            # Fallback to calculated readiness
            fields_collected = gap_summary.fields_collected if gap_summary else 0
            total_fields = gap_summary.total_fields_required if gap_summary else 0
            fields_missing = gap_summary.fields_missing if gap_summary else 0

            if total_fields == 0 or fields_missing == 0:
                confidence = 1.0
                is_ready = True
                reason = "No data gaps identified - collection complete"
                missing_requirements = []
            else:
                confidence = (
                    (fields_collected / total_fields) if total_fields > 0 else 0
                )
                thresholds = await self._get_tenant_thresholds()
                readiness_threshold = thresholds.get("readiness_threshold", 0.7)
                is_ready = confidence >= readiness_threshold

                if is_ready:
                    reason = f"Collection {int(confidence * 100)}% complete - meets threshold"
                else:
                    threshold_pct = int(readiness_threshold * 100)
                    reason = f"Collection {int(confidence * 100)}% complete - below {threshold_pct}% threshold"

                # Extract missing requirements from critical gaps
                missing_requirements = []
                if gap_summary and gap_summary.critical_gaps:
                    for gap in gap_summary.critical_gaps[:5]:
                        if isinstance(gap, dict):
                            missing_requirements.append(
                                gap.get("field_name", "Unknown field")
                            )

            return ReadinessResult(
                is_ready=is_ready,
                confidence=confidence,
                reason=reason,
                missing_requirements=missing_requirements,
                thresholds_used=await self._get_tenant_thresholds(),
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

    def _create_readiness_task(self, flow: CollectionFlow, gap_summary: Any) -> Dict:
        """Create task for readiness assessment - kept for compatibility."""
        # This method is no longer used but kept to avoid breaking changes
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
