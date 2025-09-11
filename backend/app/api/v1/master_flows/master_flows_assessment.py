"""
Master Flow Assessment API Endpoints
Assessment-specific endpoints integrated into master flows for MFO compatibility
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.api.v1.endpoints.context.services.user_service import UserService
from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter()


# Helper function to get user context with proper authentication
async def get_current_user_context(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get user context with client_account_id and engagement_id from authenticated user.
    """
    service = UserService(db)
    user_context = await service.get_user_context(current_user)

    return {
        "user_id": str(current_user.id),
        "client_account_id": (
            str(user_context.client.id) if user_context.client else None
        ),
        "engagement_id": (
            str(user_context.engagement.id) if user_context.engagement else None
        ),
    }


@router.get("/{flow_id}/assessment-status")
async def get_assessment_flow_status_via_master(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """Get assessment flow status via Master Flow Orchestrator"""

    client_account_id = context.client_account_id
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    try:
        from app.repositories.assessment_flow_repository import AssessmentFlowRepository
        from app.models.assessment_flow import AssessmentFlowStatus, AssessmentPhase

        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Calculate progress percentage
        phase_order = [
            AssessmentPhase.ARCHITECTURE_MINIMUMS,
            AssessmentPhase.COMPONENT_ANALYSIS,
            AssessmentPhase.TECH_DEBT_ANALYSIS,
            AssessmentPhase.SIX_R_DECISION,
            AssessmentPhase.FINALIZATION,
        ]

        progress_percentage = 0
        try:
            if flow_state.status == AssessmentFlowStatus.COMPLETED:
                progress_percentage = 100
            else:
                current_index = phase_order.index(flow_state.current_phase)
                progress_percentage = int(
                    ((current_index + 1) / len(phase_order)) * 100
                )
        except ValueError:
            progress_percentage = 0

        return {
            "flow_id": flow_id,
            "status": flow_state.status.value,
            "progress_percentage": progress_percentage,
            "current_phase": flow_state.current_phase.value,
            "next_phase": None,  # Will be calculated by frontend
            "phase_data": flow_state.phase_results or {},
            "selected_applications": len(flow_state.selected_application_ids or []),
            "assessment_complete": (
                flow_state.status == AssessmentFlowStatus.COMPLETED
            ),
            "created_at": flow_state.created_at.isoformat(),
            "updated_at": flow_state.updated_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get assessment status: {str(e)}"
        )


@router.get("/{flow_id}/assessment-applications")
async def get_assessment_applications_via_master(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> List[Dict[str, Any]]:
    """Get assessment flow applications via Master Flow Orchestrator"""

    client_account_id = context.client_account_id
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    try:
        from app.repositories.assessment_flow_repository import AssessmentFlowRepository
        from app.services.integrations.discovery_integration import (
            DiscoveryFlowIntegration,
        )

        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        if not flow_state.selected_application_ids:
            return []

        # Get application details using Discovery Integration
        applications = []
        discovery_integration = DiscoveryFlowIntegration()

        for app_id in flow_state.selected_application_ids:
            try:
                # Get application metadata from discovery
                metadata = await discovery_integration.get_application_metadata(
                    db, str(app_id), client_account_id
                )

                # Extract basic info for the response
                basic_info = metadata.get("basic_info", {})
                technical_info = metadata.get("technical_info", {})
                assessment_readiness = metadata.get("assessment_readiness", {})
                discovery_info = metadata.get("discovery_info", {})

                app_info = {
                    "id": basic_info.get("id", str(app_id)),
                    "name": basic_info.get("name", f"Application {app_id}"),
                    "type": basic_info.get("type"),
                    "environment": basic_info.get("environment"),
                    "business_criticality": basic_info.get("business_criticality"),
                    "technology_stack": technical_info.get("technology_stack", []),
                    "complexity_score": metadata.get("performance_metrics", {}).get(
                        "complexity_score"
                    ),
                    "readiness_score": assessment_readiness.get("score"),
                    "discovery_completed_at": discovery_info.get("completed_at"),
                }
                applications.append(app_info)

            except Exception:
                # Add fallback entry with just ID and name
                applications.append(
                    {
                        "id": str(app_id),
                        "name": f"Application {app_id}",
                        "type": None,
                        "environment": None,
                        "business_criticality": None,
                        "technology_stack": [],
                        "complexity_score": None,
                        "readiness_score": None,
                        "discovery_completed_at": None,
                    }
                )

        return applications

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get assessment applications: {str(e)}"
        )


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
        from app.repositories.assessment_flow_repository import AssessmentFlowRepository

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
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    try:
        from app.repositories.assessment_flow_repository import AssessmentFlowRepository

        repo = AssessmentFlowRepository(db, client_account_id)
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
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    try:
        from app.repositories.assessment_flow_repository import AssessmentFlowRepository

        repo = AssessmentFlowRepository(db, client_account_id)
        await repo.update_phase_data(flow_id, "architecture_standards", standards_data)

        return {
            "flow_id": flow_id,
            "phase": "architecture_standards",
            "status": "updated",
            "message": "Architecture standards updated via MFO",
        }

    except Exception as e:
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
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    try:
        from app.repositories.assessment_flow_repository import AssessmentFlowRepository
        from app.models.assessment_flow import AssessmentFlowStatus

        repo = AssessmentFlowRepository(db, client_account_id)

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
