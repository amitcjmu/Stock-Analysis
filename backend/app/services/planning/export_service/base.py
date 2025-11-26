"""
Base Export Service - Common utilities and data retrieval

Provides base class and data retrieval functionality for all export formats.

Architecture:
- Layer 2 (Service Layer): Export orchestration and format-specific generation
- Uses PlanningFlow model data for comprehensive export content

Related Issues:
- #1152 (Backend Export Service Implementation)

ADRs:
- ADR-012: Flow Status Management Separation (Two-Table Pattern)
"""

import logging
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.exceptions import FlowError
from app.models.planning import (
    PlanningFlow,
    ProjectTimeline,
    TimelinePhase,
    TimelineMilestone,
)

logger = logging.getLogger(__name__)


class BaseExportService:
    """
    Base service for exporting planning flow data.

    Provides common data retrieval functionality used by all export formats.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize export service with database session and request context.

        Args:
            db: Async SQLAlchemy database session
            context: Request context with tenant scoping
        """
        self.db = db
        self.context = context

        logger.info(
            f"BaseExportService initialized - Client: {context.client_account_id}, "
            f"Engagement: {context.engagement_id}"
        )

    async def get_full_planning_data(self, planning_flow_id: UUID) -> Dict[str, Any]:
        """
        Retrieve complete planning flow data for export.

        Aggregates data from:
        - PlanningFlow (wave plan, resources, costs)
        - ProjectTimeline (timeline structure)
        - TimelinePhase (phase details)
        - TimelineMilestone (milestone data)

        Args:
            planning_flow_id: UUID of planning flow

        Returns:
            Comprehensive planning data dictionary

        Raises:
            FlowError: If planning flow not found
        """
        try:
            # Get planning flow with tenant scoping (MANDATORY per ADR-012)
            stmt = select(PlanningFlow).where(
                and_(
                    PlanningFlow.planning_flow_id == planning_flow_id,
                    PlanningFlow.client_account_id == self.context.client_account_id,
                    PlanningFlow.engagement_id == self.context.engagement_id,
                )
            )

            result = await self.db.execute(stmt)
            planning_flow = result.scalar_one_or_none()

            if not planning_flow:
                raise FlowError(
                    f"Planning flow not found: {planning_flow_id}",
                    flow_name="planning",
                    flow_id=str(planning_flow_id),
                )

            # Get associated timeline data
            timeline_stmt = (
                select(ProjectTimeline)
                .where(
                    and_(
                        ProjectTimeline.planning_flow_id == planning_flow.id,
                        ProjectTimeline.client_account_id
                        == self.context.client_account_id,
                        ProjectTimeline.engagement_id == self.context.engagement_id,
                    )
                )
                .order_by(ProjectTimeline.created_at.desc())
            )

            timeline_result = await self.db.execute(timeline_stmt)
            timeline = timeline_result.scalar_one_or_none()

            # Get phases if timeline exists
            phases_data = []
            milestones_data = []

            if timeline:
                # Get timeline phases
                phases_stmt = (
                    select(TimelinePhase)
                    .where(
                        and_(
                            TimelinePhase.timeline_id == timeline.id,
                            TimelinePhase.client_account_id
                            == self.context.client_account_id,
                            TimelinePhase.engagement_id == self.context.engagement_id,
                        )
                    )
                    .order_by(TimelinePhase.planned_start_date)
                )

                phases_result = await self.db.execute(phases_stmt)
                phases = phases_result.scalars().all()

                phases_data = [
                    {
                        "id": str(phase.id),
                        "name": phase.phase_name,
                        "start_date": (
                            phase.planned_start_date.isoformat()
                            if phase.planned_start_date
                            else None
                        ),
                        "end_date": (
                            phase.planned_end_date.isoformat()
                            if phase.planned_end_date
                            else None
                        ),
                        "status": phase.status,
                        "progress": (
                            float(phase.progress_percentage)
                            if phase.progress_percentage
                            else 0.0
                        ),
                        "dependencies": [
                            str(pid) for pid in (phase.predecessor_phase_ids or [])
                        ],
                    }
                    for phase in phases
                ]

                # Get milestones
                milestones_stmt = (
                    select(TimelineMilestone)
                    .where(
                        and_(
                            TimelineMilestone.timeline_id == timeline.id,
                            TimelineMilestone.client_account_id
                            == self.context.client_account_id,
                            TimelineMilestone.engagement_id
                            == self.context.engagement_id,
                        )
                    )
                    .order_by(TimelineMilestone.planned_date)
                )

                milestones_result = await self.db.execute(milestones_stmt)
                milestones = milestones_result.scalars().all()

                milestones_data = [
                    {
                        "name": milestone.milestone_name,
                        "planned_date": (
                            milestone.planned_date.isoformat()
                            if milestone.planned_date
                            else None
                        ),
                        "actual_date": (
                            milestone.actual_date.isoformat()
                            if milestone.actual_date
                            else None
                        ),
                        "status": milestone.status,
                        "phase_id": (
                            str(milestone.phase_id) if milestone.phase_id else None
                        ),
                    }
                    for milestone in milestones
                ]

            # Aggregate comprehensive data
            planning_data = {
                "planning_flow_id": str(planning_flow.planning_flow_id),
                "master_flow_id": str(planning_flow.master_flow_id),
                "current_phase": planning_flow.current_phase,
                "phase_status": planning_flow.phase_status,
                "selected_applications": [
                    str(app_id) for app_id in planning_flow.selected_applications
                ],
                "wave_plan": planning_flow.wave_plan_data or {},
                "resource_allocation": planning_flow.resource_allocation_data or {},
                "timeline": {
                    "phases": phases_data,
                    "milestones": milestones_data,
                    "timeline_data": planning_flow.timeline_data or {},
                },
                "cost_estimation": planning_flow.cost_estimation_data or {},
                "planning_config": planning_flow.planning_config or {},
                "agent_execution_log": planning_flow.agent_execution_log or [],
                "warnings": planning_flow.warnings or [],
                "validation_errors": planning_flow.validation_errors or [],
                "created_at": planning_flow.created_at.isoformat(),
                "updated_at": planning_flow.updated_at.isoformat(),
                "planning_completed_at": (
                    planning_flow.planning_completed_at.isoformat()
                    if planning_flow.planning_completed_at
                    else None
                ),
            }

            logger.info(
                f"✅ Retrieved planning data: {len(planning_data['wave_plan'].get('waves', []))} waves, "
                f"{len(phases_data)} phases, {len(milestones_data)} milestones"
            )

            return planning_data

        except FlowError:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to retrieve planning data: {e}", exc_info=True)
            raise FlowError(
                f"Failed to retrieve planning data: {str(e)}",
                flow_name="planning",
                flow_id=str(planning_flow_id),
            )
