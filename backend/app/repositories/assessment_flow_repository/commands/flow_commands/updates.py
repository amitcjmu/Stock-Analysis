"""
Flow update operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, update

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

    await self.db.execute(
        update(AssessmentFlow)
        .where(
            and_(
                AssessmentFlow.id == flow_id,
                AssessmentFlow.client_account_id == self.client_account_id,
            )
        )
        .values(**update_data)
    )
    await self.db.commit()

    logger.info(f"Updated flow {flow_id} phase to {current_phase}")


async def save_user_input(self, flow_id: str, phase: str, user_input: Dict[str, Any]):
    """Save user input for specific phase"""

    # Get current user_inputs
    result = await self.db.execute(
        select(AssessmentFlow.user_inputs).where(
            and_(
                AssessmentFlow.id == flow_id,
                AssessmentFlow.client_account_id == self.client_account_id,
            )
        )
    )
    current_inputs = result.scalar() or {}
    current_inputs[phase] = user_input

    await self.db.execute(
        update(AssessmentFlow)
        .where(
            and_(
                AssessmentFlow.id == flow_id,
                AssessmentFlow.client_account_id == self.client_account_id,
            )
        )
        .values(
            user_inputs=current_inputs,
            last_user_interaction=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    )
    await self.db.commit()


async def save_agent_insights(
    self, flow_id: str, phase: str, insights: List[Dict[str, Any]]
):
    """Save agent insights for specific phase and log to master flow"""

    # Get current agent insights
    result = await self.db.execute(
        select(AssessmentFlow.agent_insights).where(
            and_(
                AssessmentFlow.id == flow_id,
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
                AssessmentFlow.id == flow_id,
                AssessmentFlow.client_account_id == self.client_account_id,
            )
        )
        .values(agent_insights=current_insights, updated_at=datetime.utcnow())
    )
    await self.db.commit()
