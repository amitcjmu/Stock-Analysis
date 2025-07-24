"""
Flow Queries - Core flow query operations
"""

import logging
import uuid
from typing import List, Optional

from app.models.assessment_flow import AssessmentFlow
from app.models.assessment_flow_state import (
    AssessmentFlowState,
    AssessmentFlowStatus,
    AssessmentPhase,
)
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class FlowQueries:
    """Queries for core assessment flow operations"""

    def __init__(self, db: AsyncSession, client_account_id: int):
        self.db = db
        self.client_account_id = client_account_id

    async def get_assessment_flow_state(
        self, flow_id: str
    ) -> Optional[AssessmentFlowState]:
        """Get complete assessment flow state with all related data"""

        # Get main flow record with eager loading
        result = await self.db.execute(
            select(AssessmentFlow)
            .options(
                selectinload(AssessmentFlow.architecture_standards),
                selectinload(AssessmentFlow.application_overrides),
                selectinload(AssessmentFlow.application_components),
                selectinload(AssessmentFlow.tech_debt_analysis),
                selectinload(AssessmentFlow.component_treatments),
                selectinload(AssessmentFlow.sixr_decisions),
                selectinload(AssessmentFlow.learning_feedback),
            )
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
        )
        flow = result.scalar_one_or_none()
        if not flow:
            return None

        # Import state queries for helper methods
        from .state_queries import StateQueries

        state_queries = StateQueries(self.db, self.client_account_id)

        # Convert to Pydantic state model
        try:
            # Get architecture standards
            arch_standards = await state_queries.get_architecture_standards(
                flow.engagement_id
            )

            # Get application overrides grouped by app
            app_overrides = await state_queries.get_application_overrides(flow_id)

            # Get application components grouped by app
            app_components = await state_queries.get_application_components(flow_id)

            # Get tech debt analysis grouped by app
            tech_debt = await state_queries.get_tech_debt_analysis(flow_id)

            # Get 6R decisions
            sixr_decisions = await state_queries.get_sixr_decisions(flow_id)

            return AssessmentFlowState(
                flow_id=flow.id,
                client_account_id=flow.client_account_id,
                engagement_id=flow.engagement_id,
                selected_application_ids=[
                    uuid.UUID(app_id) for app_id in flow.selected_application_ids
                ],
                engagement_architecture_standards=arch_standards,
                application_architecture_overrides=app_overrides,
                architecture_captured=flow.architecture_captured,
                application_components=app_components,
                tech_debt_analysis=tech_debt["analysis"],
                component_tech_debt=tech_debt["scores"],
                sixr_decisions=sixr_decisions,
                pause_points=flow.pause_points or [],
                user_inputs=flow.user_inputs or {},
                status=AssessmentFlowStatus(flow.status),
                progress=flow.progress,
                current_phase=(
                    AssessmentPhase(flow.current_phase)
                    if flow.current_phase
                    else AssessmentPhase.INITIALIZATION
                ),
                next_phase=(
                    AssessmentPhase(flow.next_phase) if flow.next_phase else None
                ),
                phase_results=flow.phase_results or {},
                agent_insights=flow.agent_insights or [],
                apps_ready_for_planning=[
                    uuid.UUID(app_id) for app_id in flow.apps_ready_for_planning
                ],
                created_at=flow.created_at,
                updated_at=flow.updated_at,
                last_user_interaction=flow.last_user_interaction,
                completed_at=flow.completed_at,
            )

        except Exception as e:
            logger.error(f"Failed to convert flow {flow_id} to state model: {str(e)}")
            raise

    async def get_flows_by_engagement(
        self, engagement_id: str, limit: int = 50
    ) -> List[AssessmentFlow]:
        """Get all assessment flows for an engagement"""

        result = await self.db.execute(
            select(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.engagement_id == engagement_id,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
            .order_by(AssessmentFlow.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_flows_by_status(
        self, status: str, limit: int = 50
    ) -> List[AssessmentFlow]:
        """Get flows by status"""

        result = await self.db.execute(
            select(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.status == status,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
            .order_by(AssessmentFlow.updated_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def search_flows_by_application(self, app_id: str) -> List[AssessmentFlow]:
        """Find flows that include a specific application"""

        result = await self.db.execute(
            select(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.selected_application_ids.contains([app_id]),
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
            .order_by(AssessmentFlow.updated_at.desc())
        )
        return result.scalars().all()
