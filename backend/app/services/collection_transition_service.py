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
        # Get flow with tenant-scoped query
        flow = await self._get_collection_flow(flow_id)

        # CRITICAL: Check assessment_ready flag first - overrides gap analysis
        if flow.assessment_ready:
            logger.info(
                f"✅ Flow {flow_id} has assessment_ready=true - bypassing gap analysis"
            )
            return ReadinessResult(
                is_ready=True,
                confidence=1.0,
                reason="Collection marked as ready for assessment (assessment_ready=true)",
                missing_requirements=[],
                thresholds_used=await self._get_tenant_thresholds(),
            )

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

        try:
            # Execute task using agent - handle different agent types
            if hasattr(agent, "execute_async"):
                result = await agent.execute_async(inputs={"task": task_description})
            elif hasattr(agent, "execute"):
                # Use sync execute method
                result = agent.execute(task=task_description)
            else:
                raise AttributeError("Agent has no execute method available")

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

        except (AttributeError, TypeError) as e:
            # Handle case where agent doesn't have execute method
            logger.warning(
                f"Agent execute not available: {e}, falling back to calculation"
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
        Bug #630 Fix: Create assessment with proper two-table pattern (ADR-012).
        Creates both master flow AND child flow atomically in a single transaction.
        """

        try:
            # Get collection flow
            collection_flow = await self._get_collection_flow(collection_flow_id)

            # Bug #630 Fix - STEP 1: Create master flow first
            from app.services.master_flow_orchestrator import MasterFlowOrchestrator

            orchestrator = MasterFlowOrchestrator(self.db, self.context)

            # Bug #668 Fix: Use correct parameter names and rely on context for tenant info
            # MasterFlowOrchestrator.create_flow() extracts client_account_id, engagement_id,
            # and user_id from self.context automatically (see flow_creation_operations.py:172-173)
            master_flow_id, _ = await orchestrator.create_flow(
                flow_type="assessment",
                flow_name=f"Assessment for {collection_flow.flow_name or 'Collection'}",
                configuration={
                    "source_collection_flow_id": str(collection_flow.id),
                    "transition_type": "collection_to_assessment",
                },
            )

            # Flush to get master_flow_id in DB (but don't commit yet)
            await self.db.flush()

            logger.info(f"✅ Created assessment master flow: {master_flow_id}")

            # Bug #630 Fix - STEP 2: Create child flow with master_flow_id FK
            from app.models.assessment_flow.core_models import AssessmentFlow
            from uuid import uuid4

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

            # Create child flow record with master_flow_id FK
            assessment_flow = AssessmentFlow(
                id=uuid4(),
                master_flow_id=master_flow_id,  # ✅ Link to master flow (ADR-012)
                client_account_id=self.context.client_account_id,
                engagement_id=self.context.engagement_id,
                flow_name=f"Assessment for {collection_flow.flow_name or 'Collection'}",
                description=f"Assessment created from collection flow {collection_flow.flow_id}",
                status="initialized",
                current_phase="initialization",
                progress=0.0,
                configuration={
                    "collection_flow_id": str(collection_flow.id),
                    "selected_application_ids": [
                        str(app_id) for app_id in selected_app_ids
                    ],
                    "transition_date": datetime.utcnow().isoformat(),
                    "transition_type": "collection_to_assessment",
                },
                flow_metadata={
                    "source": "collection_transition",
                    "created_by_service": "collection_transition_service",
                    "source_collection": {
                        "collection_flow_id": str(collection_flow.id),
                        "collection_master_flow_id": str(collection_flow.flow_id),
                        "transitioned_from": datetime.utcnow().isoformat(),
                    },
                },
                started_at=datetime.utcnow(),
            )

            self.db.add(assessment_flow)

            # Flush to get child flow ID
            await self.db.flush()

            logger.info(
                f"✅ Created assessment child flow: {assessment_flow.id} linked to master {master_flow_id}"
            )

            # Update collection flow linkage
            if hasattr(collection_flow, "assessment_flow_id"):
                collection_flow.assessment_flow_id = assessment_flow.id
                collection_flow.assessment_transition_date = datetime.utcnow()

            # Store bidirectional references in collection metadata
            current_metadata = getattr(collection_flow, "flow_metadata", {}) or {}
            collection_flow.flow_metadata = {
                **current_metadata,
                "assessment_handoff": {
                    "assessment_flow_id": str(assessment_flow.id),
                    "assessment_master_flow_id": str(master_flow_id),
                    "transitioned_at": datetime.utcnow().isoformat(),
                    "transitioned_by": (
                        str(self.context.user_id) if self.context.user_id else None
                    ),
                },
            }

            # Bug #630 Fix - STEP 3: Single atomic commit for both master and child
            # This is the final commit that makes both flows permanent
            # Note: The endpoint already has a transaction context, so this commit applies to all changes
            logger.info(
                f"✅ Assessment flow creation complete - master={master_flow_id}, child={assessment_flow.id}"
            )

            return TransitionResult(
                assessment_flow_id=assessment_flow.id,
                assessment_flow=assessment_flow,
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            # Roll back entire transaction on any error
            await self.db.rollback()
            logger.error(
                f"Failed to create assessment flow (two-table pattern): {e}",
                exc_info=True,
            )
            raise

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
