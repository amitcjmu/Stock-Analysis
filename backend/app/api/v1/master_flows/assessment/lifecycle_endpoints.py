"""
Assessment lifecycle endpoints.

Endpoints for initializing, resuming, updating, and finalizing assessment flows.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db

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

        return {
            "flow_id": str(assessment_flow_id),
            "status": "initialized",
            "message": "Assessment flow created via MFO",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize assessment: {str(e)}"
        )


@router.post("/{flow_id}/assessment/resume")
async def resume_assessment_flow_via_mfo(
    flow_id: str,
    user_input: Dict[str, Any],
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

        repo = AssessmentFlowRepository(db, client_account_id, engagement_id)
        result = await repo.resume_flow(flow_id, user_input)

        return {
            "flow_id": flow_id,
            "status": "resumed",
            "current_phase": result.get("current_phase"),
            "progress": result.get("progress_percentage"),
        }

    except Exception as e:
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

        return {
            "flow_id": flow_id,
            "phase": "architecture_standards",
            "status": "updated",
            "message": "Architecture standards updated via MFO",
        }

    except Exception as e:
        logger.error(
            f"Failed to update architecture standards: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to update standards: {str(e)}"
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

        return {
            "flow_id": flow_id,
            "status": "completed",
            "apps_ready_for_planning": apps_to_finalize,
            "message": "Assessment finalized via MFO",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to finalize assessment: {str(e)}"
        )
