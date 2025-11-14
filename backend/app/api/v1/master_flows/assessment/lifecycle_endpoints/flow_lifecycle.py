"""
Flow lifecycle endpoints: initialize, resume, finalize.

Handles core lifecycle operations for assessment flows.
"""

import logging
from typing import Any, Dict, List

from fastapi import BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.utils.json_sanitization import sanitize_for_json

from . import router

logger = logging.getLogger(__name__)


@router.post("/{flow_id}/assessment/initialize")
async def initialize_assessment_flow_via_mfo(
    flow_id: str,
    selected_application_ids: List[str],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Initialize assessment flow through MFO.

    Per 7-layer architecture: Uses service layer for business logic orchestration.
    """

    client_account_id = context.client_account_id
    engagement_id = context.engagement_id
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    try:
        from app.services.assessment.assessment_flow_lifecycle_service import (
            AssessmentFlowLifecycleService,
        )

        # Initialize service layer (handles orchestration)
        service = AssessmentFlowLifecycleService(db=db, context=context)

        # Create assessment flow via service (not repository)
        assessment_flow_id = await service.create_assessment_flow(
            engagement_id=engagement_id,
            selected_application_ids=selected_application_ids,
            created_by=context.user_id,
        )

        return sanitize_for_json(
            {
                "flow_id": str(assessment_flow_id),
                "status": "initialized",
                "message": "Assessment flow created via MFO",
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize assessment: {str(e)}"
        )


@router.post("/{flow_id}/assessment/resume")
async def resume_assessment_flow_via_mfo(
    flow_id: str,
    request_body: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Resume assessment flow phase through MFO.

    Per 7-layer architecture: Uses service layer for business logic orchestration.
    """

    client_account_id = context.client_account_id
    engagement_id = context.engagement_id
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")
    if not engagement_id:
        raise HTTPException(status_code=400, detail="Engagement ID required")

    try:
        from app.services.assessment.assessment_flow_lifecycle_service import (
            AssessmentFlowLifecycleService,
        )
        from app.repositories.assessment_flow_repository import (
            AssessmentFlowRepository,
        )
        from app.models.assessment_flow import AssessmentPhase
        from app.api.v1.endpoints import assessment_flow_processors

        # Extract user_input from request body (unwrap double-nesting)
        user_input = request_body.get("user_input", request_body)
        logger.info(f"Resuming assessment flow {flow_id} with user_input: {user_input}")

        # Initialize service layer (handles orchestration)
        service = AssessmentFlowLifecycleService(db=db, context=context)

        # [ISSUE-999] AUTO-RECOVERY: Check for zombie flow BEFORE resuming
        # Repository still provides read access for this check
        repo = AssessmentFlowRepository(db, client_account_id, engagement_id)
        assessment_flow = await repo.get_by_flow_id(flow_id)
        if assessment_flow:
            is_zombie = (
                assessment_flow.progress >= 80
                and (
                    not assessment_flow.phase_results
                    or assessment_flow.phase_results == {}
                )
                and (
                    not assessment_flow.agent_insights
                    or assessment_flow.agent_insights == []
                )
            )

            if is_zombie:
                logger.warning(
                    f"[ISSUE-999-ZOMBIE] 🧟 AUTO-RECOVERY: Detected zombie flow {flow_id} "
                    f"at {assessment_flow.progress}% with EMPTY results. "
                    f"Current phase: {assessment_flow.current_phase}. "
                    f"Will force agent re-execution..."
                )

        # Resume flow via service (not repository)
        result = await service.resume_flow(flow_id, user_input)

        # Get current phase to trigger agent execution
        current_phase_str = result.get("current_phase")

        # FIX FOR ISSUE #999: Ensure background task is ALWAYS added for agent execution
        # unless we're at the finalization phase (which has no agents to run)
        logger.info(
            f"[ISSUE-999] Resume flow result: flow_id={flow_id}, "
            f"phase={current_phase_str}, status={result.get('status')}, "
            f"progress={result.get('progress_percentage')}%"
        )

        if current_phase_str:
            try:
                current_phase = AssessmentPhase(current_phase_str)

                # Skip background task for finalization phase (no agents needed)
                if current_phase == AssessmentPhase.FINALIZATION:
                    logger.info(
                        "[ISSUE-999] Skipping agent execution for finalization phase"
                    )
                else:
                    # Trigger background task for agent execution
                    logger.info(
                        f"[ISSUE-999] Adding background task for phase {current_phase.value}"
                    )
                    background_tasks.add_task(
                        assessment_flow_processors.continue_assessment_flow,
                        flow_id,
                        str(client_account_id),  # Ensure string type
                        str(engagement_id),  # Ensure string type
                        current_phase,
                        str(context.user_id),  # Ensure string type
                    )
                    logger.info(
                        f"[ISSUE-999] ✅ Successfully queued background agent execution for phase {current_phase.value}"
                    )
            except ValueError as e:
                logger.error(
                    f"[ISSUE-999] Invalid phase '{current_phase_str}' - ValueError: {e}. "
                    f"This will prevent agent execution! Please check phase enum values."
                )
        else:
            logger.warning(
                f"[ISSUE-999] No current_phase in result - cannot trigger agent execution. "
                f"Result keys: {list(result.keys())}"
            )

        return sanitize_for_json(
            {
                "flow_id": flow_id,
                "status": "resumed",
                "current_phase": result.get("current_phase"),
                "progress": result.get("progress_percentage"),
            }
        )

    except Exception as e:
        logger.error(
            f"Failed to resume assessment flow {flow_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to resume assessment: {str(e)}"
        )


@router.post("/{flow_id}/assessment/finalize")
async def finalize_assessment_via_mfo(
    flow_id: str,
    finalization_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """Finalize assessment and prepare for planning through MFO"""

    client_account_id = context.client_account_id
    engagement_id = context.engagement_id
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")
    if not engagement_id:
        raise HTTPException(status_code=400, detail="Engagement ID required")

    try:
        from app.repositories.assessment_flow_repository import (
            AssessmentFlowRepository,
        )
        from app.models.assessment_flow import AssessmentFlowStatus

        repo = AssessmentFlowRepository(db, client_account_id, engagement_id)

        # Update flow status to completed
        await repo.update_flow_status(flow_id, AssessmentFlowStatus.COMPLETED)

        # Mark applications as ready for planning
        apps_to_finalize = finalization_data.get("apps_to_finalize", [])
        await repo.mark_apps_ready_for_planning(flow_id, apps_to_finalize)

        return sanitize_for_json(
            {
                "flow_id": flow_id,
                "status": "completed",
                "apps_ready_for_planning": apps_to_finalize,
                "message": "Assessment finalized via MFO",
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to finalize assessment: {str(e)}"
        )
