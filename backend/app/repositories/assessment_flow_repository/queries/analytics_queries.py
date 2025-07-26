"""
Analytics Queries - Analytics and reporting queries
"""

import logging
from typing import Any, Dict

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import (
    ApplicationComponent,
    AssessmentFlow,
    SixRDecision,
    TechDebtAnalysis,
)

logger = logging.getLogger(__name__)


class AnalyticsQueries:
    """Queries for analytics and reporting operations"""

    def __init__(self, db: AsyncSession, client_account_id: int):
        self.db = db
        self.client_account_id = client_account_id

    async def get_flow_analytics(self, flow_id: str) -> Dict[str, Any]:
        """Get analytics data for a flow"""

        # Get basic flow info
        flow_result = await self.db.execute(
            select(AssessmentFlow).where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
        )
        flow = flow_result.scalar_one_or_none()
        if not flow:
            return {}

        # Get strategy distribution
        strategy_result = await self.db.execute(
            select(SixRDecision.overall_strategy, func.count(SixRDecision.id))
            .where(SixRDecision.assessment_flow_id == flow_id)
            .group_by(SixRDecision.overall_strategy)
        )
        strategy_distribution = dict(strategy_result.fetchall())

        # Get tech debt severity distribution
        debt_result = await self.db.execute(
            select(TechDebtAnalysis.severity, func.count(TechDebtAnalysis.id))
            .where(TechDebtAnalysis.assessment_flow_id == flow_id)
            .group_by(TechDebtAnalysis.severity)
        )
        debt_distribution = dict(debt_result.fetchall())

        # Get component type distribution
        component_result = await self.db.execute(
            select(
                ApplicationComponent.component_type, func.count(ApplicationComponent.id)
            )
            .where(ApplicationComponent.assessment_flow_id == flow_id)
            .group_by(ApplicationComponent.component_type)
        )
        component_distribution = dict(component_result.fetchall())

        return {
            "flow_summary": {
                "id": str(flow.id),
                "status": flow.status,
                "progress": flow.progress,
                "current_phase": flow.current_phase,
                "total_applications": len(flow.selected_application_ids),
                "apps_ready_for_planning": len(flow.apps_ready_for_planning or []),
            },
            "strategy_distribution": strategy_distribution,
            "tech_debt_distribution": debt_distribution,
            "component_distribution": component_distribution,
            "created_at": flow.created_at.isoformat(),
            "updated_at": flow.updated_at.isoformat(),
        }
