"""
Flow resumption operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import and_, select, update

from app.models.assessment_flow import AssessmentFlow
from app.models.assessment_flow_state import AssessmentFlowStatus

logger = logging.getLogger(__name__)


async def resume_flow(self, flow_id: str, user_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resume assessment flow from pause point, advance to next phase.
    Per ADR-027: Uses FlowTypeConfig as single source of truth for phase progression.
    Supports legacy phase names via phase alias normalization.
    """

    # Per ADR-027: Get flow configuration from registry
    from app.services.flow_type_registry import flow_type_registry
    from app.services.flow_configs.phase_aliases import normalize_phase_name

    flow_config = flow_type_registry.get_flow_config("assessment")

    # Get current flow state
    result = await self.db.execute(
        select(AssessmentFlow).where(
            and_(
                AssessmentFlow.id == flow_id,
                AssessmentFlow.client_account_id == self.client_account_id,
            )
        )
    )
    flow = result.scalar_one_or_none()

    if not flow:
        raise ValueError(f"Assessment flow {flow_id} not found")

    current_phase = flow.current_phase

    # Normalize legacy phase names to ADR-027 canonical names
    try:
        normalized_current_phase = normalize_phase_name("assessment", current_phase)
        logger.info(f"Normalized phase {current_phase} -> {normalized_current_phase}")
    except ValueError as e:
        # Phase not recognized - log warning and keep original
        logger.warning(f"Could not normalize phase {current_phase}: {e}. Using as-is.")
        normalized_current_phase = current_phase

    # Per ADR-027: Use FlowTypeConfig.get_next_phase() instead of hardcoded array
    next_phase = flow_config.get_next_phase(normalized_current_phase)

    if not next_phase:
        # Already at final phase, stay at current
        next_phase = normalized_current_phase
        logger.info(
            f"Flow {flow_id} already at final phase: {normalized_current_phase}"
        )

    # Per ADR-027: Calculate progress using FlowTypeConfig.get_phase_index()
    total_phases = len(flow_config.phases)
    next_phase_index = flow_config.get_phase_index(next_phase)

    if next_phase_index >= 0:
        progress_percentage = int(((next_phase_index + 1) / total_phases) * 100)
    else:
        # Phase not found in config - use current progress
        progress_percentage = flow.progress or 0
        logger.warning(
            f"Phase {next_phase} not found in flow config, keeping current progress"
        )

    # Save user input for current phase
    current_inputs = flow.user_inputs or {}
    current_inputs[current_phase] = user_input

    # Update flow to next phase
    await self.db.execute(
        update(AssessmentFlow)
        .where(
            and_(
                AssessmentFlow.id == flow_id,
                AssessmentFlow.client_account_id == self.client_account_id,
            )
        )
        .values(
            current_phase=next_phase,
            status=AssessmentFlowStatus.IN_PROGRESS.value,
            progress=progress_percentage,
            user_inputs=current_inputs,
            last_user_interaction=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    )
    await self.db.commit()

    logger.info(
        f"Resumed flow {flow_id}: {current_phase} -> {next_phase} ({progress_percentage}%)"
    )

    return {
        "flow_id": flow_id,
        "current_phase": next_phase,
        "previous_phase": current_phase,
        "progress_percentage": progress_percentage,
        "status": AssessmentFlowStatus.IN_PROGRESS.value,
    }
