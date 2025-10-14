"""Phase transition logic for collection flows."""

import logging
from typing import Any, Dict, List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow
from app.models.collection_flow.schemas import CollectionFlowStatus, CollectionPhase

logger = logging.getLogger(__name__)


async def transition_to_gap_analysis(
    db: AsyncSession,
    collection_flow: CollectionFlow,
    normalized_ids: List[str],
    flow_id: str,
    context: RequestContext,
    processed_count: int,
    normalized_records_count: int,
) -> Dict[str, Any]:
    """Transition collection flow to gap analysis phase.

    CRITICAL FIX: Gap analysis phase is UI-driven and should NOT auto-invoke MFO agents.
    This endpoint only updates the phase and returns immediately, allowing the frontend
    to navigate to the gap-analysis page where users can manually trigger AI analysis.

    Args:
        db: Database session
        collection_flow: Collection flow object
        normalized_ids: List of selected application IDs
        flow_id: Collection flow ID string
        context: Request context with tenant scoping
        processed_count: Number of applications processed
        normalized_records_count: Number of normalized records created

    Returns:
        Response dict with transition results
    """
    if not collection_flow.master_flow_id:
        logger.error(
            f"Collection flow {flow_id} has no master_flow_id - cannot transition phases"
        )
        # Per Qodo review: Use 409 Conflict instead of 500 for state conflicts
        raise HTTPException(
            status_code=409,
            detail={
                "error": "flow_initialization_incomplete",
                "message": "Flow not properly initialized with Master Flow Orchestrator",
                "flow_id": flow_id,
                "suggestion": (
                    "This indicates a system error during flow creation. "
                    "Please delete this flow and create a new one."
                ),
                "debug_info": {
                    "has_master_flow_id": False,
                    "current_phase": collection_flow.current_phase,
                    "status": collection_flow.status,
                },
            },
        )

    # CRITICAL FIX: Do NOT invoke MFO for gap_analysis phase
    # Gap analysis is UI-driven - agents only triggered via explicit user action
    # (e.g., "Perform Agentic Analysis" button on AI Grid)
    if collection_flow.current_phase == CollectionPhase.ASSET_SELECTION.value:
        # Update collection flow phase without triggering agents
        collection_flow.current_phase = CollectionPhase.GAP_ANALYSIS.value
        # Per ADR-012: Set status to PAUSED (waiting for user to review gaps on AI Grid)
        collection_flow.status = CollectionFlowStatus.PAUSED.value
        await db.commit()

        logger.info(
            f"Transitioned collection flow {flow_id} from ASSET_SELECTION to "
            f"GAP_ANALYSIS (skipping MFO - UI-driven phase)"
        )

        # CRITICAL FIX: Return collection flow ID (not master flow ID)
        # Frontend must navigate to collection flow ID for gap analysis page
        return {
            "success": True,
            "message": (
                f"Successfully updated collection flow with {processed_count} "
                f"applications, created {normalized_records_count} normalized records, "
                "and transitioned to gap analysis phase"
            ),
            "flow_id": str(
                collection_flow.id
            ),  # Use collection flow ID, not input flow_id
            "master_flow_id": (
                str(collection_flow.master_flow_id)
                if collection_flow.master_flow_id
                else None
            ),
            "selected_application_count": processed_count,
            "normalized_records_created": normalized_records_count,
            "mfo_execution_triggered": False,
            "execution_result": {
                "status": "skipped",
                "reason": (
                    "Gap analysis is UI-driven - agents only invoked via "
                    "manual user action on AI Grid"
                ),
            },
        }

    # If not in asset_selection phase, just return current state
    logger.info(
        f"Collection flow {flow_id} already in phase {collection_flow.current_phase} - "
        "no transition needed"
    )
    # CRITICAL FIX: Return collection flow ID (not master flow ID)
    return {
        "success": True,
        "message": (
            f"Successfully updated collection flow with {processed_count} "
            f"applications, created {normalized_records_count} normalized records"
        ),
        "flow_id": str(collection_flow.id),  # Use collection flow ID, not input flow_id
        "master_flow_id": (
            str(collection_flow.master_flow_id)
            if collection_flow.master_flow_id
            else None
        ),
        "selected_application_count": processed_count,
        "normalized_records_created": normalized_records_count,
        "mfo_execution_triggered": False,
        "execution_result": {
            "status": "skipped",
            "reason": f"Already in phase {collection_flow.current_phase}",
        },
    }
