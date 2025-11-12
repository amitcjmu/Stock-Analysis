"""
Assessment Flow Recovery Endpoint

Provides mechanisms to recover "zombie flows" - assessment flows stuck at high
completion percentages with empty results due to background tasks never executing.

Related: GitHub Issue #999 - Assessment flow zombie flows
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models.assessment_flow import AssessmentPhase
from app.repositories.assessment_flow_repository import AssessmentFlowRepository
from app.utils.json_sanitization import sanitize_for_json

logger = logging.getLogger(__name__)

router = APIRouter()


def is_zombie_flow(
    progress: int,
    phase_results: Dict[str, Any],
    agent_insights: list,
) -> bool:
    """
    Detect if a flow is a "zombie" - stuck at high completion with empty results.

    A zombie flow has:
    - Progress >= 80% (indicates phase should be complete)
    - Empty phase_results dict (no agent output stored)
    - Empty agent_insights list (no agent analysis recorded)

    Args:
        progress: Flow completion percentage (0-100)
        phase_results: Dictionary of phase execution results
        agent_insights: List of agent analysis insights

    Returns:
        True if flow is a zombie, False otherwise
    """
    return (
        progress >= 80
        and (not phase_results or phase_results == {})
        and (not agent_insights or agent_insights == [])
    )


@router.post("/{flow_id}/recover")
async def recover_stuck_assessment_flow(
    flow_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Manually recover assessment flows stuck at high completion with empty results.

    This endpoint detects "zombie flows" that show high progress (>=80%)
    but have empty phase_results and agent_insights, indicating agents
    never executed. It re-queues background tasks to complete the flow.

    **Zombie Flow Symptoms:**
    - Progress shows 80-100% complete
    - phase_results is empty dict: `{}`
    - agent_insights is empty array: `[]`
    - No 6R recommendations in Asset table
    - No [ISSUE-999] log entries for background task execution

    **Recovery Process:**
    1. Detects if flow matches zombie criteria
    2. Identifies current phase from flow state
    3. Queues background task to re-execute agents for that phase
    4. Agents populate phase_results, agent_insights, and 6R recommendations

    Args:
        flow_id: UUID of the assessment flow to recover
        background_tasks: FastAPI background tasks queue
        db: Database session
        context: Request context with tenant info

    Returns:
        Recovery status including whether recovery was needed and queued

    Raises:
        HTTPException 404: If assessment flow not found
        HTTPException 400: If tenant context is invalid

    Related: GitHub Issue #999
    """
    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")
    if not engagement_id:
        raise HTTPException(status_code=400, detail="Engagement ID required")

    try:
        repo = AssessmentFlowRepository(db, client_account_id, engagement_id)
        flow = await repo.get_by_flow_id(flow_id)

        if not flow:
            raise HTTPException(
                status_code=404,
                detail=f"Assessment flow {flow_id} not found",
            )

        # Check if flow is a zombie (high progress but empty results)
        zombie_detected = is_zombie_flow(
            flow.progress,
            flow.phase_results or {},
            flow.agent_insights or [],
        )

        if not zombie_detected:
            logger.info(
                f"[ISSUE-999-RECOVERY] Flow {flow_id} is NOT a zombie. "
                f"Progress: {flow.progress}%, "
                f"phase_results entries: {len(flow.phase_results or {})}, "
                f"agent_insights count: {len(flow.agent_insights or [])}"
            )
            return sanitize_for_json(
                {
                    "message": "Flow does not appear to be stuck (zombie detection failed)",
                    "flow_id": flow_id,
                    "progress": flow.progress,
                    "phase_results_count": len(flow.phase_results or {}),
                    "agent_insights_count": len(flow.agent_insights or []),
                    "recovery_needed": False,
                    "zombie_criteria": {
                        "progress_threshold": 80,
                        "requires_empty_results": True,
                        "requires_empty_insights": True,
                    },
                }
            )

        # Zombie detected - queue recovery
        logger.warning(
            f"[ISSUE-999-RECOVERY] 🧟 ZOMBIE FLOW DETECTED: {flow_id} "
            f"at {flow.progress}% with EMPTY results. "
            f"Current phase: {flow.current_phase}. Initiating recovery..."
        )

        # Parse current phase to AssessmentPhase enum
        try:
            current_phase = AssessmentPhase(flow.current_phase)
        except ValueError as e:
            logger.error(
                f"[ISSUE-999-RECOVERY] Invalid phase '{flow.current_phase}' "
                f"for flow {flow_id}: {e}. Cannot recover."
            )
            raise HTTPException(
                status_code=400,
                detail=f"Invalid current_phase '{flow.current_phase}'. "
                f"Cannot determine which agents to execute.",
            )

        # Queue background task to re-execute agents for current phase
        from app.api.v1.endpoints import assessment_flow_processors

        background_tasks.add_task(
            assessment_flow_processors.continue_assessment_flow,
            flow_id=str(flow.id),
            client_account_id=str(client_account_id),
            engagement_id=str(engagement_id),
            phase=current_phase,
            user_id=str(context.user_id),
        )

        logger.info(
            f"[ISSUE-999-RECOVERY] ✅ Recovery task queued for zombie flow {flow_id}. "
            f"Will re-execute agents for phase: {current_phase.value}"
        )

        return sanitize_for_json(
            {
                "message": "Recovery initiated for stuck assessment flow",
                "flow_id": flow_id,
                "progress": flow.progress,
                "current_phase": flow.current_phase,
                "recovery_queued": True,
                "zombie_detected": True,
                "recovery_action": f"Re-executing agents for {current_phase.value} phase",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[ISSUE-999-RECOVERY] Failed to recover flow {flow_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Recovery failed: {str(e)}",
        )
