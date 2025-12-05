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
from app.services.flow_orchestration.phase_execution_lock_manager import (
    phase_lock_manager,
)

from . import router

logger = logging.getLogger(__name__)


async def _validate_canonical_applications_exist(
    db: AsyncSession,
    assessment_flow: Any,
    client_account_id: str,
    engagement_id: str,
    flow_id: str,
) -> None:
    """
    [ISSUE-719] Pre-validate that selected canonical applications exist in database.

    Raises HTTPException 409 if any selected apps are missing.
    Extracted to reduce cyclomatic complexity of resume_assessment_flow_via_mfo.
    """
    from uuid import UUID
    from sqlalchemy import select
    from app.models.canonical_applications.canonical_application import (
        CanonicalApplication,
    )

    # Get selected canonical app IDs from the assessment flow
    selected_app_ids = assessment_flow.selected_canonical_application_ids or []

    # Fallback: Try application_asset_groups if new field is empty
    if not selected_app_ids and assessment_flow.application_asset_groups:
        selected_app_ids = [
            group.get("canonical_application_id")
            for group in assessment_flow.application_asset_groups
            if group.get("canonical_application_id")
        ]

    if not selected_app_ids:
        return  # No apps to validate

    # Query which apps exist in canonical_applications table
    app_uuids = [
        UUID(app_id) if isinstance(app_id, str) else app_id
        for app_id in selected_app_ids
    ]
    stmt = select(CanonicalApplication.id).where(
        CanonicalApplication.id.in_(app_uuids),
        CanonicalApplication.client_account_id == UUID(client_account_id),
        CanonicalApplication.engagement_id == UUID(engagement_id),
    )
    result_query = await db.execute(stmt)
    found_ids = {str(row[0]) for row in result_query.fetchall()}

    # Identify missing apps
    apps_not_found = [
        str(app_id) for app_id in selected_app_ids if str(app_id) not in found_ids
    ]

    if apps_not_found:
        logger.error(
            f"[ISSUE-719] Data integrity error: {len(apps_not_found)} of "
            f"{len(selected_app_ids)} selected canonical applications not found "
            f"in database for flow {flow_id}: {apps_not_found}"
        )
        # Return HTTP 409 Conflict with details for frontend to display
        raise HTTPException(
            status_code=409,
            detail={
                "error": "data_integrity_error",
                "message": f"{len(apps_not_found)} selected applications not found in database. "
                f"Please start a new assessment with valid applications.",
                "apps_not_found": apps_not_found,
                "total_selected": len(selected_app_ids),
                "flow_id": flow_id,
            },
        )


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

                # [ISSUE-719] PRE-VALIDATION: Check data integrity BEFORE queueing background task
                if (
                    current_phase == AssessmentPhase.RECOMMENDATION_GENERATION
                    and assessment_flow
                ):
                    await _validate_canonical_applications_exist(
                        db=db,
                        assessment_flow=assessment_flow,
                        client_account_id=client_account_id,
                        engagement_id=engagement_id,
                        flow_id=flow_id,
                    )

                # Skip background task for finalization phase (no agents needed)
                if current_phase == AssessmentPhase.FINALIZATION:
                    logger.info(
                        "[ISSUE-999] Skipping agent execution for finalization phase"
                    )
                else:
                    # CRITICAL (Issue #999): Check lock BEFORE queueing background task
                    # Prevents duplicate phase executions from rapid resume calls
                    if not await phase_lock_manager.try_acquire_lock(
                        str(flow_id), current_phase.value
                    ):
                        logger.info(
                            f"[ISSUE-999] Phase {current_phase.value} already executing "
                            f"for flow {flow_id}, skipping duplicate background task"
                        )
                        # Return current status without queueing duplicate
                        return sanitize_for_json(
                            {
                                "flow_id": flow_id,
                                "status": "already_running",
                                "current_phase": current_phase.value,
                                "progress": result.get("progress_percentage"),
                                "message": f"Phase {current_phase.value} is already executing",
                            }
                        )

                    # Trigger background task for agent execution
                    logger.info(
                        f"[ISSUE-999] ✅ Lock acquired, adding background task for phase {current_phase.value}"
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

    except HTTPException:
        # Re-raise HTTPExceptions (like our 409 data integrity error) as-is
        raise
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


@router.post("/{flow_id}/assessment/initiate-decommission")
async def initiate_decommission_from_assessment(
    flow_id: str,
    request_body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    GAP-5 FIX: Create decommission flow for applications marked as 'Retire' in assessment.

    This endpoint is the integration hook between Assessment Flow and Decommission Flow.
    When an assessment identifies applications to retire (6R = Retire), this endpoint
    creates a linked decommission flow for proper system retirement tracking.

    Args:
        flow_id: Assessment flow ID (source of 6R decisions)
        request_body: Contains:
            - application_ids: List of application IDs marked for retirement
            - flow_name: Optional name for the decommission flow

    Returns:
        Decommission flow creation result with flow_id
    """
    client_account_id = context.client_account_id
    engagement_id = context.engagement_id
    user_id = context.user_id

    if not client_account_id or not engagement_id:
        raise HTTPException(
            status_code=400, detail="Client account ID and Engagement ID required"
        )

    try:
        from uuid import UUID
        from app.repositories.assessment_flow_repository import AssessmentFlowRepository
        from app.api.v1.endpoints.decommission_flow.mfo_integration.create import (
            create_decommission_via_mfo,
        )

        # Extract application IDs to retire
        application_ids = request_body.get("application_ids", [])
        flow_name = request_body.get("flow_name")

        if not application_ids:
            raise HTTPException(
                status_code=400,
                detail="At least one application ID is required for decommission",
            )

        # Verify assessment flow exists and applications have Retire decision
        repo = AssessmentFlowRepository(db, client_account_id, engagement_id)
        sixr_decisions = await repo.get_all_sixr_decisions(flow_id)

        # Validate that requested applications have 'retire' 6R decision
        retire_strategies = ["retire", "retain"]  # Both can be decommissioned
        apps_to_decommission = []
        invalid_apps = []

        for app_id in application_ids:
            decision = sixr_decisions.get(app_id, {})
            strategy = (
                decision.get("sixr_strategy", "") or decision.get("strategy", "") or ""
            ).lower()

            if strategy in retire_strategies:
                apps_to_decommission.append(app_id)
            else:
                invalid_apps.append(
                    {
                        "application_id": app_id,
                        "current_strategy": strategy or "not_found",
                    }
                )

        if invalid_apps:
            logger.warning(
                f"Some applications don't have Retire/Retain strategy: {invalid_apps}"
            )
            # Continue with valid apps, warn about invalid ones
            if not apps_to_decommission:
                raise HTTPException(
                    status_code=400,
                    detail=f"No applications have Retire or Retain strategy. "
                    f"Invalid apps: {invalid_apps}",
                )

        # Convert string IDs to UUIDs
        system_uuids = [UUID(app_id) for app_id in apps_to_decommission]

        # Create decommission flow via MFO
        decommission_result = await create_decommission_via_mfo(
            client_account_id=UUID(client_account_id),
            engagement_id=UUID(engagement_id),
            system_ids=system_uuids,
            user_id=str(user_id) if user_id else "system",
            flow_name=flow_name or f"Decommission from Assessment {flow_id[:8]}",
            decommission_strategy={
                "source_assessment_flow_id": flow_id,
                "initiated_from": "assessment_6r_retire",
                "original_decisions": {
                    app_id: sixr_decisions.get(app_id, {})
                    for app_id in apps_to_decommission
                },
            },
            db=db,
        )

        return sanitize_for_json(
            {
                "assessment_flow_id": flow_id,
                "decommission_flow_id": decommission_result.get("flow_id"),
                "decommission_master_flow_id": decommission_result.get(
                    "master_flow_id"
                ),
                "applications_to_decommission": apps_to_decommission,
                "skipped_applications": invalid_apps,
                "status": "decommission_created",
                "message": f"Created decommission flow for {len(apps_to_decommission)} applications",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to initiate decommission from assessment {flow_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate decommission from assessment: {str(e)}",
        )
