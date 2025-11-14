"""
Query endpoints for assessment lifecycle.

Handles read operations for phase status and completion checking.
"""

import logging
from typing import Any, Dict

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.utils.json_sanitization import sanitize_for_json

from . import router

logger = logging.getLogger(__name__)


@router.get("/{flow_id}/assessment/phase/{phase_name}/status")
async def get_phase_completion_status(
    flow_id: str,
    phase_name: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Check if a specific phase has completed and saved results.

    This endpoint is used by frontend to verify phase execution completed
    before updating UI state (Fix for Issue #1048).

    Returns:
        - status: "completed" if phase_results contains this phase, "pending" otherwise
        - results: Phase execution results if completed, None otherwise
    """
    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    if not client_account_id or not engagement_id:
        raise HTTPException(
            status_code=400, detail="Client account and engagement ID required"
        )

    try:
        from app.repositories.assessment_flow_repository.commands.flow_commands.phase_results import (
            PhaseResultsPersistence,
        )

        persistence = PhaseResultsPersistence(db, client_account_id, engagement_id)

        # Get phase results for this phase
        phase_results = await persistence.get_phase_results(flow_id, phase_name)

        if phase_results and phase_results != {}:
            return sanitize_for_json(
                {
                    "status": "completed",
                    "phase_name": phase_name,
                    "results": phase_results,
                    "completed_at": phase_results.get("persisted_at"),
                }
            )
        else:
            return sanitize_for_json(
                {
                    "status": "pending",
                    "phase_name": phase_name,
                    "results": None,
                }
            )

    except Exception as e:
        logger.error(f"Failed to get phase status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to check phase status: {str(e)}"
        )
