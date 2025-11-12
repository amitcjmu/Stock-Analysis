"""
Flow resumption operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import and_, or_, select, update

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
    # CRITICAL (Bug #999): Support both child flow ID and master_flow_id
    result = await self.db.execute(
        select(AssessmentFlow).where(
            and_(
                or_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.master_flow_id == flow_id,
                ),
                AssessmentFlow.client_account_id == self.client_account_id,
            )
        )
    )
    flow = result.scalar_one_or_none()

    if not flow:
        raise ValueError(f"Assessment flow {flow_id} not found")

    current_phase = flow.current_phase
    user_expected_phase = user_input.get("phase")

    # ENHANCED LOGGING for bug #724 investigation
    logger.info(
        f"[BUG-724] resume_flow START - flow_id={flow_id}, "
        f"current_phase='{current_phase}', "
        f"user_expected_phase='{user_expected_phase}', "
        f"status={flow.status}, "
        f"progress={flow.progress}"
    )

    # CRITICAL FIX: Validate that user's expected phase matches database current phase
    # This prevents the flow from auto-progressing ahead of user interaction
    if user_expected_phase and user_expected_phase != current_phase:
        logger.warning(
            f"[PHASE-MISMATCH] User expected phase '{user_expected_phase}' "
            f"but database shows '{current_phase}'. Resetting flow to user's phase."
        )
        # Reset flow to the phase the user thinks they're on
        await self.db.execute(
            update(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id,
                )
            )
            .values(
                current_phase=user_expected_phase,
                updated_at=datetime.utcnow(),
            )
        )
        await self.db.commit()
        current_phase = user_expected_phase
        logger.info(f"[PHASE-MISMATCH] Reset flow {flow_id} to phase '{current_phase}'")

    # Normalize legacy phase names to ADR-027 canonical names
    try:
        normalized_current_phase = normalize_phase_name("assessment", current_phase)
        logger.info(
            f"[BUG-724] Phase normalization SUCCESS: "
            f"'{current_phase}' -> '{normalized_current_phase}'"
        )
    except ValueError as e:
        # Phase not recognized - log warning and keep original
        logger.warning(
            f"[BUG-724] Phase normalization FAILED for '{current_phase}': {e}. "
            f"Using original phase name as-is."
        )
        normalized_current_phase = current_phase

    # Per ADR-027: Use FlowTypeConfig.get_next_phase() instead of hardcoded array
    next_phase = flow_config.get_next_phase(normalized_current_phase)

    logger.info(
        f"[BUG-724] get_next_phase('{normalized_current_phase}') returned: "
        f"'{next_phase}' (None means phase not found in config)"
    )

    if not next_phase:
        # Already at final phase, stay at current
        next_phase = normalized_current_phase
        logger.warning(
            f"[BUG-724] EDGE CASE DETECTED - get_next_phase returned None! "
            f"Flow {flow_id} staying at current phase: {normalized_current_phase}. "
            f"This may indicate phase is not in FlowTypeConfig.phases list."
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
        f"[BUG-724] resume_flow COMPLETE - flow_id={flow_id}, "
        f"transition: '{current_phase}' -> '{next_phase}', "
        f"progress: {progress_percentage}%, "
        f"phase_index: {next_phase_index}/{total_phases}"
    )

    return {
        "flow_id": flow_id,
        "current_phase": next_phase,
        "previous_phase": current_phase,
        "progress_percentage": progress_percentage,
        "status": AssessmentFlowStatus.IN_PROGRESS.value,
    }
