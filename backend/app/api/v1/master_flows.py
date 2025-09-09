"""
Master Flow Coordination API Endpoints
Task 5.2.1: API endpoints for cross-phase asset queries and master flow analytics
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.api.v1.endpoints.context.services.user_service import UserService
from app.api.v1.master_flows_schemas import (
    CrossPhaseAnalyticsResponse,
    DiscoveryFlowResponse,
    MasterFlowCoordinationResponse,
    MasterFlowSummaryResponse,
)
from app.api.v1.master_flows_service import MasterFlowService
from app.core.database import get_db
from app.models import User
from app.repositories.asset_repository import AssetRepository
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.schemas.asset_schemas import AssetResponse

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


# Static routes first (no path parameters)


@router.get("/analytics/cross-phase", response_model=CrossPhaseAnalyticsResponse)
async def get_cross_phase_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> CrossPhaseAnalyticsResponse:
    """Get analytics across all phases and master flows"""

    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    asset_repo = AssetRepository(db, client_account_id)

    try:
        analytics = await asset_repo.get_cross_phase_analytics()
        return CrossPhaseAnalyticsResponse(**analytics)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving cross-phase analytics: {str(e)}"
        )


@router.get("/active", response_model=List[Dict[str, Any]])
async def get_active_master_flows(
    flow_type: Optional[str] = Query(
        None,
        alias="flow_type",  # Accept snake_case from frontend
        description="Filter by flow type (discovery, assessment, planning, execution, etc.)",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> List[Dict[str, Any]]:
    """Get all active master flows across all flow types"""

    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    service = MasterFlowService(
        db=db,
        client_account_id=client_account_id,
        engagement_id=current_user.get("engagement_id"),
        user_id=current_user.get("user_id"),
    )

    try:
        return await service.get_active_master_flows(flow_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving active master flows: {str(e)}"
        )


@router.get("/coordination/summary", response_model=MasterFlowCoordinationResponse)
async def get_master_flow_coordination_summary(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> MasterFlowCoordinationResponse:
    """Get master flow coordination summary"""

    client_account_id = current_user.get("client_account_id")
    engagement_id = current_user.get("engagement_id")

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    discovery_repo = DiscoveryFlowRepository(
        db, client_account_id, engagement_id, user_id=current_user.get("user_id")
    )

    try:
        summary = await discovery_repo.get_master_flow_coordination_summary()
        return MasterFlowCoordinationResponse(**summary)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving coordination summary: {str(e)}"
        )


@router.get("/phase/{phase}/assets", response_model=List[AssetResponse])
async def get_assets_by_phase(
    phase: str,
    current_phase: bool = Query(
        True,
        description="If true, filter by current_phase; if false, filter by source_phase",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> List[AssetResponse]:
    """Get assets by phase (current or source)"""

    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    asset_repo = AssetRepository(db, client_account_id)

    try:
        if current_phase:
            assets = await asset_repo.get_by_current_phase(phase)
        else:
            assets = await asset_repo.get_by_source_phase(phase)

        return [AssetResponse.from_orm(asset) for asset in assets]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving assets by phase: {str(e)}"
        )


@router.get("/multi-phase/assets", response_model=List[AssetResponse])
async def get_multi_phase_assets(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> List[AssetResponse]:
    """Get assets that have progressed through multiple phases"""

    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    asset_repo = AssetRepository(db, client_account_id)

    try:
        assets = await asset_repo.get_multi_phase_assets()
        return [AssetResponse.from_orm(asset) for asset in assets]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving multi-phase assets: {str(e)}"
        )


# Dynamic routes (with path parameters) - must come after static routes


@router.get("/{master_flow_id}/assets", response_model=List[AssetResponse])
async def get_assets_by_master_flow(
    master_flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> List[AssetResponse]:
    """Get all assets for a specific master flow"""

    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    asset_repo = AssetRepository(db, client_account_id)

    try:
        assets = await asset_repo.get_by_master_flow(master_flow_id)
        return [AssetResponse.from_orm(asset) for asset in assets]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving assets: {str(e)}"
        )


@router.get("/{master_flow_id}/summary", response_model=MasterFlowSummaryResponse)
async def get_master_flow_summary(
    master_flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> MasterFlowSummaryResponse:
    """Get comprehensive summary for a master flow"""

    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    asset_repo = AssetRepository(db, client_account_id)

    try:
        summary = await asset_repo.get_master_flow_summary(master_flow_id)
        return MasterFlowSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving master flow summary: {str(e)}"
        )


@router.get("/{master_flow_id}/discovery-flow", response_model=DiscoveryFlowResponse)
async def get_discovery_flow_by_master(
    master_flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> DiscoveryFlowResponse:
    """Get discovery flow associated with a master flow"""

    client_account_id = current_user.get("client_account_id")
    engagement_id = current_user.get("engagement_id")

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    discovery_repo = DiscoveryFlowRepository(
        db, client_account_id, engagement_id, user_id=current_user.get("user_id")
    )

    try:
        discovery_flow = await discovery_repo.get_by_master_flow_id(master_flow_id)
        if not discovery_flow:
            raise HTTPException(
                status_code=404, detail="Discovery flow not found for master flow"
            )

        return DiscoveryFlowResponse.from_orm(discovery_flow)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving discovery flow: {str(e)}"
        )


@router.post("/{discovery_flow_id}/transition-to-assessment")
async def transition_to_assessment_phase(
    discovery_flow_id: str,
    assessment_flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> Dict[str, Any]:
    """Prepare discovery flow for assessment phase transition"""

    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    service = MasterFlowService(
        db=db,
        client_account_id=client_account_id,
        engagement_id=current_user.get("engagement_id"),
        user_id=current_user.get("user_id"),
    )

    try:
        return await service.transition_to_assessment_phase(
            discovery_flow_id, assessment_flow_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error transitioning to assessment: {str(e)}"
        )


# Assessment flow endpoints - integrated into master flows for MFO compatibility
@router.get("/{flow_id}/assessment-status")
async def get_assessment_flow_status_via_master(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> Dict[str, Any]:
    """Get assessment flow status via Master Flow Orchestrator"""

    client_account_id = current_user.get("client_account_id")
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
    current_user: dict = Depends(get_current_user_context),
) -> List[Dict[str, Any]]:
    """Get assessment flow applications via Master Flow Orchestrator"""

    client_account_id = current_user.get("client_account_id")
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


# Assessment Phase Operations - MFO Proxy Endpoints


@router.post("/{flow_id}/assessment/initialize")
async def initialize_assessment_flow_via_mfo(
    flow_id: str,
    selected_application_ids: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> Dict[str, Any]:
    """Initialize assessment flow through MFO"""

    client_account_id = current_user.get("client_account_id")
    engagement_id = current_user.get("engagement_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    try:
        from app.repositories.assessment_flow_repository import AssessmentFlowRepository

        repo = AssessmentFlowRepository(
            db, client_account_id, engagement_id, user_id=current_user.get("user_id")
        )

        # Create assessment flow with MFO registration
        assessment_flow_id = await repo.create_assessment_flow(
            engagement_id=engagement_id,
            selected_application_ids=selected_application_ids,
            created_by=current_user.get("user_id"),
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
    current_user: dict = Depends(get_current_user_context),
) -> Dict[str, Any]:
    """Resume assessment flow phase through MFO"""

    client_account_id = current_user.get("client_account_id")
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
    current_user: dict = Depends(get_current_user_context),
) -> Dict[str, Any]:
    """Update architecture standards through MFO"""

    client_account_id = current_user.get("client_account_id")
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
    current_user: dict = Depends(get_current_user_context),
) -> Dict[str, Any]:
    """Finalize assessment and prepare for planning through MFO"""

    client_account_id = current_user.get("client_account_id")
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


@router.put("/{asset_id}/phase-progression")
async def update_asset_phase_progression(
    asset_id: str,
    new_phase: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> Dict[str, Any]:
    """Update an asset's phase progression"""

    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    service = MasterFlowService(
        db=db,
        client_account_id=client_account_id,
        engagement_id=current_user.get("engagement_id"),
        user_id=current_user.get("user_id"),
    )

    try:
        return await service.update_asset_phase(asset_id, new_phase)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating asset phase: {str(e)}"
        )


@router.delete("/{flow_id}")
async def soft_delete_master_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> Dict[str, Any]:
    """
    Soft delete a master flow and mark all its child flows as deleted.
    """
    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    service = MasterFlowService(
        db=db,
        client_account_id=client_account_id,
        engagement_id=current_user.get("engagement_id"),
        user_id=current_user.get("user_id"),
    )

    try:
        return await service.soft_delete_flow(flow_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting master flow: {str(e)}"
        )
