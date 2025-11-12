"""
Assessment lifecycle endpoints.

Endpoints for initializing, resuming, updating, and finalizing assessment flows.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.utils.json_sanitization import sanitize_for_json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{flow_id}/assessment/initialize")
async def initialize_assessment_flow_via_mfo(
    flow_id: str,
    selected_application_ids: List[str],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """Initialize assessment flow through MFO"""

    client_account_id = context.client_account_id
    engagement_id = context.engagement_id
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    try:
        from app.repositories.assessment_flow_repository import (
            AssessmentFlowRepository,
        )

        repo = AssessmentFlowRepository(
            db, client_account_id, engagement_id, user_id=context.user_id
        )

        # Create assessment flow with MFO registration
        assessment_flow_id = await repo.create_assessment_flow(
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
    """Resume assessment flow phase through MFO"""

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
        from app.models.assessment_flow import AssessmentPhase
        from app.api.v1.endpoints import assessment_flow_processors

        # Extract user_input from request body (unwrap double-nesting)
        user_input = request_body.get("user_input", request_body)
        logger.info(f"Resuming assessment flow {flow_id} with user_input: {user_input}")

        repo = AssessmentFlowRepository(db, client_account_id, engagement_id)

        # [ISSUE-999] AUTO-RECOVERY: Check for zombie flow BEFORE resuming
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

        result = await repo.resume_flow(flow_id, user_input)

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


@router.put("/{flow_id}/assessment/architecture-standards")
async def update_architecture_standards_via_mfo(
    flow_id: str,
    standards_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """Update architecture standards through MFO"""

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
        from app.models.assessment_flow_state import ArchitectureRequirement

        repo = AssessmentFlowRepository(db, client_account_id, engagement_id)

        # Extract engagement standards from request
        engagement_standards = standards_data.get("engagement_standards", [])

        # Convert engagement standards to ArchitectureRequirement objects
        arch_requirements = []
        for std in engagement_standards:
            # Fix P0: Convert supported_versions from list to dict if needed
            supported_vers = std.get("supported_versions", {})
            if isinstance(supported_vers, list):
                # Frontend may send empty list, convert to empty dict
                supported_vers = (
                    {} if not supported_vers else {v: v for v in supported_vers}
                )

            arch_req = ArchitectureRequirement(
                requirement_type=std.get("requirement_type"),
                description=std.get("description"),
                mandatory=std.get("mandatory", False),
                supported_versions=supported_vers,
                requirement_details=std.get("requirement_details", {}),
                created_by=context.user_id,
            )
            arch_requirements.append(arch_req)

        # Save engagement-level standards
        if arch_requirements:
            await repo.save_architecture_standards(engagement_id, arch_requirements)

        return sanitize_for_json(
            {
                "flow_id": flow_id,
                "phase": "architecture_standards",
                "status": "updated",
                "message": "Architecture standards updated via MFO",
            }
        )

    except Exception as e:
        logger.error(
            f"Failed to update architecture standards: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to update standards: {str(e)}"
        )


@router.put("/{flow_id}/assessment/phase-data")
async def update_assessment_phase_data(
    flow_id: str,
    phase_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Update phase-specific data (components, tech debt items, etc.)
    Fix for issue #641 - Missing endpoint for component creation
    """

    client_account_id = context.client_account_id
    engagement_id = context.engagement_id
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")
    if not engagement_id:
        raise HTTPException(status_code=400, detail="Engagement ID required")

    try:
        from app.models.assessment_flow.component_models import ApplicationComponent
        from uuid import UUID

        # Extract phase and data from request
        phase = phase_data.get("phase")
        data = phase_data.get("data", {})

        logger.info(
            f"Updating phase data for flow {flow_id}, phase: {phase}, data keys: {list(data.keys())}"
        )

        # Handle component_analysis phase (placeholder)
        if phase == "component_analysis":
            # Placeholder for component analysis data
            return sanitize_for_json(
                {
                    "flow_id": flow_id,
                    "phase": phase,
                    "status": "updated",
                    "message": "Component analysis data updated",
                }
            )

        # Handle tech_debt_analysis phase - FIX FOR ISSUE #641
        elif phase == "tech_debt_analysis":
            app_id = data.get("app_id")
            components = data.get("components", [])

            if not app_id:
                raise HTTPException(
                    status_code=400,
                    detail="app_id is required for tech_debt_analysis phase",
                )

            # Validate UUID formats (Qodo Bot suggestion #3)
            try:
                flow_uuid = UUID(flow_id)
                app_uuid = UUID(app_id)
            except ValueError as uuid_err:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid UUID format for flow_id '{flow_id}' or app_id '{app_id}': {str(uuid_err)}",
                )

            # Store components for this application
            stored_components = []
            for comp_data in components:
                # Validate required component fields (Qodo Bot suggestion #2)
                component_name = comp_data.get("name")
                component_type = comp_data.get("type")

                if not component_name or not component_type:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Component data is missing required fields 'name' or 'type': {comp_data}",
                    )

                # Security: Validate input size limits (Qodo Bot security issue)
                if len(component_name) > 255:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Component name exceeds 255 character limit: {len(component_name)} chars",
                    )

                description = comp_data.get("description")
                if description and len(description) > 2000:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Description exceeds 2000 character limit: {len(description)} chars",
                    )

                # Create ApplicationComponent instance
                component = ApplicationComponent(
                    assessment_flow_id=flow_uuid,
                    application_id=app_uuid,
                    component_name=component_name,
                    component_type=component_type,
                    description=description,
                    current_technology=comp_data.get("technology"),
                    configuration=comp_data.get("configuration", {}),
                    discovered_by="manual",
                    # Multi-tenant scoping (from code review)
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                )
                db.add(component)
                stored_components.append(
                    {
                        "name": component.component_name,
                        "type": component.component_type,
                    }
                )

            await db.commit()

            return sanitize_for_json(
                {
                    "flow_id": flow_id,
                    "phase": phase,
                    "status": "updated",
                    "components_stored": len(stored_components),
                    "message": f"Stored {len(stored_components)} components for application {app_id}",
                }
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported phase: {phase}. Supported phases: component_analysis, tech_debt_analysis",
            )

    except HTTPException:
        raise
    except Exception as e:
        # Qodo Bot suggestion #1 - Add rollback on error
        await db.rollback()
        logger.error(
            f"Failed to update phase data for flow {flow_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to update phase data: {str(e)}"
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
