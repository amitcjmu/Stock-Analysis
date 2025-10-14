"""
Phase-specific handlers for collection flow management.

Extracted from management.py to maintain file length under 400 lines.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.secure_logging import safe_log_format
from app.models.collection_flow.schemas import CollectionFlowStatus

logger = logging.getLogger(__name__)


async def handle_gap_analysis_phase(
    collection_flow: Any,
    flow_id: str,
    has_applications: bool,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Handle gap_analysis phase progression without triggering MFO agents.

    Args:
        collection_flow: The collection flow model instance
        flow_id: Collection flow ID for logging
        has_applications: Whether applications are selected
        db: Database session

    Returns:
        Response dictionary with phase progression status
    """
    from app.models.collection_flow.collection_flow_gaps import CollectionFlowGap

    try:
        # Check for unresolved gaps using direct query
        unresolved_count_stmt = (
            select(func.count())
            .select_from(CollectionFlowGap)
            .where(
                CollectionFlowGap.collection_flow_id == collection_flow.id,
                CollectionFlowGap.resolution_status.in_(["unresolved", "pending"]),
            )
        )
        unresolved_result = await db.execute(unresolved_count_stmt)
        unresolved_gaps = unresolved_result.scalar() or 0

        # Always allow progression from gap_analysis
        # Gaps are recommendations, not blockers
        next_phase = collection_flow.get_next_phase()
        if next_phase:
            logger.info(
                safe_log_format(
                    "Progressing from gap_analysis to {next_phase} "
                    "({unresolved_gaps} unresolved gaps remain)",
                    flow_id=flow_id,
                    next_phase=next_phase,
                    unresolved_gaps=unresolved_gaps,
                )
            )
            collection_flow.current_phase = next_phase
            collection_flow.status = CollectionFlowStatus.RUNNING
            collection_flow.updated_at = datetime.now(timezone.utc)
            await db.commit()

            action_status = "phase_progressed"
            if unresolved_gaps == 0:
                action_description = (
                    f"Gap analysis complete - progressed to {next_phase}"
                )
            else:
                action_description = (
                    f"Proceeding to {next_phase} with {unresolved_gaps} "
                    f"unresolved gaps (data can be collected manually)"
                )

            logger.info(
                safe_log_format(
                    "Returning after gap_analysis progression - "
                    "phase {next_phase} will be handled on next navigation",
                    flow_id=flow_id,
                    next_phase=next_phase,
                )
            )
            return {
                "status": "success",
                "message": "Gap analysis complete - progressed to next phase",
                "flow_id": flow_id,
                "action_status": action_status,
                "action_description": action_description,
                "current_phase": next_phase,
                "flow_status": CollectionFlowStatus.RUNNING,
                "has_applications": has_applications,
                "mfo_execution_triggered": False,
                "mfo_result": {
                    "status": "phase_progressed",
                    "reason": f"Gap analysis complete - progressed from gap_analysis to {next_phase}",
                },
                "next_steps": [],
                "continued_at": datetime.now(timezone.utc).isoformat(),
                "master_flow_id": (
                    str(collection_flow.master_flow_id)
                    if collection_flow.master_flow_id
                    else None
                ),
                "recovery_performed": bool(
                    collection_flow.flow_metadata
                    and collection_flow.flow_metadata.get("recovery_info")
                ),
                "resume_result": {
                    "status": "phase_progressed",
                    "from_phase": "gap_analysis",
                    "to_phase": next_phase,
                },
            }
        else:
            return {
                "action_status": "gap_analysis_complete",
                "action_description": f"Gap analysis reviewed ({unresolved_gaps} gaps) but no next phase defined",
            }
    except Exception as gap_check_error:
        logger.warning(
            safe_log_format(
                "Failed to check gap status for flow {flow_id}: {error}",
                flow_id=flow_id,
                error=str(gap_check_error),
            )
        )
        # Fallback: still allow progression
        next_phase = collection_flow.get_next_phase()
        if next_phase:
            collection_flow.current_phase = next_phase
            collection_flow.status = CollectionFlowStatus.RUNNING
            collection_flow.updated_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(
                safe_log_format(
                    "Gap analysis fallback progression to {next_phase}",
                    flow_id=flow_id,
                    next_phase=next_phase,
                )
            )
            return {
                "status": "success",
                "message": "Gap analysis complete - progressed to next phase (fallback)",
                "flow_id": flow_id,
                "action_status": "phase_progressed_fallback",
                "action_description": f"Gap analysis complete - progressed to {next_phase}",
                "current_phase": next_phase,
                "flow_status": CollectionFlowStatus.RUNNING,
                "has_applications": has_applications,
                "mfo_execution_triggered": False,
                "mfo_result": {
                    "status": "phase_progressed",
                    "reason": f"Gap analysis fallback progression to {next_phase}",
                },
                "next_steps": [],
                "continued_at": datetime.now(timezone.utc).isoformat(),
                "master_flow_id": (
                    str(collection_flow.master_flow_id)
                    if collection_flow.master_flow_id
                    else None
                ),
                "recovery_performed": bool(
                    collection_flow.flow_metadata
                    and collection_flow.flow_metadata.get("recovery_info")
                ),
                "resume_result": {
                    "status": "phase_progressed",
                    "from_phase": "gap_analysis",
                    "to_phase": next_phase,
                    "fallback": True,
                },
            }
        # If fallback fails, return partial status for main function to handle
        return {
            "action_status": "gap_analysis",
            "action_description": "Gap analysis complete - proceeding to manual collection",
        }
