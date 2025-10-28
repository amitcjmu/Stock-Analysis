"""
Assessment list and status endpoints.

Endpoints for listing assessment flows and getting status information.
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, cast, String

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models import User
from app.utils.json_sanitization import sanitize_for_json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/list")
async def list_assessment_flows_via_mfo(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> List[Dict[str, Any]]:
    """List all assessment flows for current tenant via Master Flow Orchestrator"""

    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    if not engagement_id:
        raise HTTPException(status_code=400, detail="Engagement ID required")

    try:
        from app.models.assessment_flow import AssessmentFlow
        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

        # Get all flows for the engagement with user information
        stmt = (
            select(AssessmentFlow, User)
            .outerjoin(
                CrewAIFlowStateExtensions,
                AssessmentFlow.id == CrewAIFlowStateExtensions.flow_id,
            )
            .outerjoin(
                User,
                CrewAIFlowStateExtensions.user_id == cast(User.id, String),
            )
            .where(
                and_(
                    AssessmentFlow.engagement_id == UUID(engagement_id),
                    AssessmentFlow.client_account_id == UUID(client_account_id),
                )
            )
            .order_by(AssessmentFlow.created_at.desc())
        )

        result_rows = await db.execute(stmt)
        flows_with_users = result_rows.all()

        # Transform to frontend format
        result = []
        for flow, user in flows_with_users:
            # Build user display name from joined user data
            if user:
                if user.first_name and user.last_name:
                    created_by = f"{user.first_name} {user.last_name}"
                elif user.email:
                    created_by = user.email
                elif user.username:
                    created_by = user.username
                else:
                    created_by = "Unknown User"
            else:
                created_by = "System"

            result.append(
                {
                    "id": str(flow.id),
                    "status": flow.status,
                    "current_phase": flow.current_phase or "initialization",
                    "progress": flow.progress or 0,
                    "selected_applications": len(flow.selected_application_ids or []),
                    "created_at": flow.created_at.isoformat(),
                    "updated_at": flow.updated_at.isoformat(),
                    "created_by": created_by,
                }
            )

        logger.info(
            f"Retrieved {len(result)} assessment flows for engagement {engagement_id}"
        )
        return sanitize_for_json(result)

    except Exception as e:
        logger.error(f"Failed to list assessment flows: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list assessment flows: {str(e)}"
        )


@router.get("/{flow_id}/assessment-status")
async def get_assessment_flow_status_via_master(  # noqa: C901 - Pre-existing complexity, refactor in separate PR
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """Get assessment flow status via Master Flow Orchestrator"""

    client_account_id = context.client_account_id
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    try:
        from app.repositories.assessment_flow_repository import (
            AssessmentFlowRepository,
        )
        from app.models.assessment_flow import AssessmentFlowStatus

        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Calculate progress percentage using FlowTypeConfig (ADR-027)
        from app.services.flow_type_registry_helpers import get_flow_config

        # Initialize variables before try block to ensure they're in scope
        progress_percentage = 0
        phase_failed = False

        try:
            config = get_flow_config("assessment")
            phase_names = [phase.name for phase in config.phases]

            # Get current phase as string
            current_phase_str = (
                flow_state.current_phase.value
                if hasattr(flow_state.current_phase, "value")
                else str(flow_state.current_phase)
            )

            # Normalize phase name to handle aliases (Fix for issue #629)
            from app.services.flow_configs.phase_aliases import normalize_phase_name

            try:
                normalized_phase = normalize_phase_name("assessment", current_phase_str)
            except ValueError:
                # Phase not recognized, use original
                normalized_phase = current_phase_str

            # Calculate progress based on phase_results, checking for failures (Fix for issue #810)
            completed_phases = 0

            if flow_state.phase_results:
                # Check each phase in order for actual completion vs failure
                for phase_name in phase_names:
                    if phase_name not in flow_state.phase_results:
                        # Haven't reached this phase yet
                        break

                    phase_data = flow_state.phase_results.get(phase_name, {})
                    phase_status = phase_data.get("status", "").lower()

                    if phase_status == "failed":
                        # Phase failed - progress stops here, don't count this phase
                        phase_failed = True
                        error_msg = phase_data.get("error", "Unknown error")
                        logger.warning(
                            f"Phase '{phase_name}' failed for flow {flow_id}: "
                            f"{error_msg}"
                        )
                        break
                    elif phase_status in ["completed", "success", "done"]:
                        # Phase successfully completed
                        completed_phases += 1
                    else:
                        # Phase not yet complete (in_progress, pending, etc.)
                        break

                # Calculate progress based on completed phases
                if len(phase_names) > 0:
                    progress_percentage = int(
                        (completed_phases / len(phase_names)) * 100
                    )
            else:
                # Fallback to current_phase index if no phase_results
                if flow_state.status == AssessmentFlowStatus.COMPLETED:
                    progress_percentage = 100
                elif normalized_phase in phase_names:
                    current_index = phase_names.index(normalized_phase)
                    progress_percentage = int(
                        ((current_index + 1) / len(phase_names)) * 100
                    )
                else:
                    # Phase not in config, default to 0
                    logger.warning(
                        f"Phase '{current_phase_str}' (normalized: '{normalized_phase}') not found in assessment config"
                    )
                    progress_percentage = 0

        except Exception as e:
            logger.error(f"Error calculating progress: {e}")
            progress_percentage = 0

        # Determine status - keep original flow status (Fix for issue #818)
        status_value = (
            flow_state.status.value
            if hasattr(flow_state.status, "value")
            else str(flow_state.status)
        )

        # Instead of overriding status, provide phase failure information separately
        failed_phases_list = []
        if phase_failed:
            # Collect list of failed phases for transparency
            failed_phases_list = [
                phase_name
                for phase_name in phase_names
                if flow_state.phase_results.get(phase_name, {})
                .get("status", "")
                .lower()
                == "failed"
            ]
            logger.info(
                f"Flow {flow_id} has phase failures "
                f"({', '.join(failed_phases_list)}) but status remains '{status_value}'"
            )

        return sanitize_for_json(
            {
                "flow_id": flow_id,
                "status": status_value,
                "has_failed_phases": phase_failed,
                "failed_phases": failed_phases_list,
                "progress_percentage": progress_percentage,
                "current_phase": (
                    flow_state.current_phase.value
                    if hasattr(flow_state.current_phase, "value")
                    else str(flow_state.current_phase)
                ),
                "next_phase": None,  # Will be calculated by frontend
                "phase_data": flow_state.phase_results or {},
                "application_count": len(flow_state.selected_application_ids or []),
                "assessment_complete": (
                    flow_state.status == AssessmentFlowStatus.COMPLETED
                ),
                "created_at": flow_state.created_at.isoformat(),
                "updated_at": flow_state.updated_at.isoformat(),
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get assessment status: {str(e)}"
        )
