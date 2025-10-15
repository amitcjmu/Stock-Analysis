"""
Master Flow Assessment API Endpoints
Assessment-specific endpoints integrated into master flows for MFO compatibility
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

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

    # Check if platform admin
    is_platform_admin = getattr(user_context.user, "is_platform_admin", False)

    return {
        "user_id": str(current_user.id),
        "client_account_id": (
            str(user_context.client.id) if user_context.client else None
        ),
        "engagement_id": (
            str(user_context.engagement.id) if user_context.engagement else None
        ),
        "is_platform_admin": is_platform_admin,
    }


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
        from sqlalchemy import select, and_

        # Get all flows for the engagement with user information
        # Join with crewai_flow_state_extensions to get user_id, then join with users
        stmt = (
            select(AssessmentFlow, User)
            .outerjoin(
                CrewAIFlowStateExtensions,
                AssessmentFlow.id == CrewAIFlowStateExtensions.flow_id,
            )
            .outerjoin(
                User,
                CrewAIFlowStateExtensions.user_id == str(User.id),
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
        return result

    except Exception as e:
        logger.error(f"Failed to list assessment flows: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list assessment flows: {str(e)}"
        )


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
        from app.models.canonical_applications import CollectionFlowApplication
        from sqlalchemy import select, and_

        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        if not flow_state.selected_application_ids:
            return []

        # CC: Check if asset-to-canonical resolution is complete by querying collection_flow_applications
        # Per refactor design: Use existing collection infrastructure instead of removed asset_resolution_service

        # CRITICAL FIX: Assessment flow_id ≠ Collection flow_id!
        # Lookup collection_flow_id from assessment's flow_metadata.source_collection
        collection_flow_id = None
        if flow_state.flow_metadata and isinstance(flow_state.flow_metadata, dict):
            source_collection = flow_state.flow_metadata.get("source_collection", {})
            if isinstance(source_collection, dict):
                collection_flow_id = source_collection.get("collection_flow_id")

        if not collection_flow_id:
            # No collection reference found - assessment may not have been created from collection
            logger.warning(
                f"Assessment flow {flow_id} has no source_collection metadata - "
                f"cannot check unmapped assets. May be standalone assessment."
            )
            # Skip asset resolution check for standalone assessments
            unmapped_assets = []
        else:
            # Query for unmapped assets using correct collection_flow_id
            unmapped_stmt = select(CollectionFlowApplication).where(
                and_(
                    CollectionFlowApplication.collection_flow_id
                    == UUID(collection_flow_id),
                    CollectionFlowApplication.asset_id.is_not(None),
                    CollectionFlowApplication.canonical_application_id.is_(None),
                    CollectionFlowApplication.client_account_id
                    == UUID(client_account_id),
                    CollectionFlowApplication.engagement_id == flow_state.engagement_id,
                )
            )
            unmapped_result = await db.execute(unmapped_stmt)
            unmapped_assets = unmapped_result.scalars().all()

        if unmapped_assets:
            # Return structured response indicating resolution needed
            logger.warning(
                f"Asset resolution incomplete for flow {flow_id}: "
                f"{len(unmapped_assets)} unmapped assets"
            )
            return [
                {
                    "resolution_required": True,
                    "unmapped_count": len(unmapped_assets),
                    "total_count": len(flow_state.selected_application_ids),
                    "message": "Asset-to-canonical application mapping must be completed before accessing applications",
                }
            ]

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
    engagement_id = context.engagement_id
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")
    if not engagement_id:
        raise HTTPException(status_code=400, detail="Engagement ID required")

    try:
        from app.repositories.assessment_flow_repository import AssessmentFlowRepository
        from app.models.assessment_flow_state import ArchitectureRequirement

        repo = AssessmentFlowRepository(db, client_account_id)

        # Extract engagement standards from request
        engagement_standards = standards_data.get("engagement_standards", [])
        # TODO: Handle application_overrides when needed
        # application_overrides = standards_data.get("application_overrides", {})

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
