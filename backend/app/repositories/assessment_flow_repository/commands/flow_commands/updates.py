"""
Flow update operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_, select, update
from uuid import UUID

from app.models.assessment_flow import AssessmentFlow

logger = logging.getLogger(__name__)


async def update_flow_phase(
    self,
    flow_id: str,
    current_phase: str,
    next_phase: Optional[str] = None,
    progress: Optional[int] = None,
    status: Optional[str] = None,
):
    """Update flow phase and progress, sync with master flow"""

    update_data = {"current_phase": current_phase, "updated_at": datetime.utcnow()}

    if next_phase:
        update_data["next_phase"] = next_phase
    if progress is not None:
        update_data["progress"] = progress
    if status:
        update_data["status"] = status

    # MFO Pattern: flow_id can be either AssessmentFlow.id OR master_flow_id
    flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id

    await self.db.execute(
        update(AssessmentFlow)
        .where(
            and_(
                or_(
                    AssessmentFlow.id == flow_uuid,
                    AssessmentFlow.master_flow_id == flow_uuid,
                ),
                AssessmentFlow.client_account_id == self.client_account_id,
            )
        )
        .values(**update_data)
    )
    await self.db.commit()

    logger.info(f"Updated flow {flow_id} phase to {current_phase}")


async def save_user_input(self, flow_id: str, phase: str, user_input: Dict[str, Any]):
    """
    Save user input for specific phase using atomic JSONB merge.

    Uses PostgreSQL's || operator to prevent race conditions (Qodo review fix).
    This is safer than read-modify-write as it's atomic at the database level.
    """
    # MFO Pattern: flow_id can be either AssessmentFlow.id OR master_flow_id
    flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id

    await self.db.execute(
        update(AssessmentFlow)
        .where(
            and_(
                or_(
                    AssessmentFlow.id == flow_uuid,
                    AssessmentFlow.master_flow_id == flow_uuid,
                ),
                AssessmentFlow.client_account_id == self.client_account_id,
            )
        )
        .values(
            # Use JSONB || operator for atomic merge (prevents race conditions)
            user_inputs=AssessmentFlow.user_inputs.op("||")({phase: user_input}),
            last_user_interaction=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    )
    await self.db.commit()


async def save_agent_insights(
    self, flow_id: str, phase: str, insights: List[Dict[str, Any]]
):
    """Save agent insights for specific phase and log to master flow"""
    # MFO Pattern: flow_id can be either AssessmentFlow.id OR master_flow_id
    flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id

    # Get current agent insights
    result = await self.db.execute(
        select(AssessmentFlow.agent_insights).where(
            and_(
                or_(
                    AssessmentFlow.id == flow_uuid,
                    AssessmentFlow.master_flow_id == flow_uuid,
                ),
                AssessmentFlow.client_account_id == self.client_account_id,
            )
        )
    )
    current_insights = result.scalar() or []

    # Add phase context to insights
    phase_insights = [
        {**insight, "phase": phase, "timestamp": datetime.utcnow().isoformat()}
        for insight in insights
    ]
    current_insights.extend(phase_insights)

    await self.db.execute(
        update(AssessmentFlow)
        .where(
            and_(
                or_(
                    AssessmentFlow.id == flow_uuid,
                    AssessmentFlow.master_flow_id == flow_uuid,
                ),
                AssessmentFlow.client_account_id == self.client_account_id,
            )
        )
        .values(agent_insights=current_insights, updated_at=datetime.utcnow())
    )
    await self.db.commit()
