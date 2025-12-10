"""
Dependency analysis endpoints for assessment flows.
Handles dependency graph retrieval and analysis execution via MFO.
Uses MFO integration layer per ADR-006 (Master Flow Orchestrator pattern).

CRITICAL: Follows MFO Flow ID Pattern from mfo_two_table_flow_id_pattern_critical.md
- URL may receive MASTER flow ID or CHILD flow ID (frontend uses master_flow_id)
- Query uses OR condition to match both master_flow_id and id
- MFO expects MASTER flow ID (extracted from child.master_flow_id)
- phase_input includes CHILD flow ID for persistence
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format
from app.models.assessment_flow import AssessmentFlow
from app.repositories.dependency_repository import DependencyRepository
from .dependency_helpers import (
    build_empty_dependency_response,
    populate_application_dependencies,
    build_dependency_graph,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class UpdateDependenciesRequest(BaseModel):
    """Request model for updating application dependencies."""

    application_id: str
    dependencies: Optional[str] = None  # Comma-separated asset IDs, None to clear


@router.get("/{flow_id}/dependency/analysis")
async def get_dependency_analysis(
    flow_id: str,  # ← CHILD flow ID from URL
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Get dependency analysis graph for assessment flow.

    Returns dependency graph with full metadata for selected applications:
    - Application-to-server dependencies
    - Application-to-application dependencies
    - Agent analysis results (if phase executed)

    **CRITICAL PATTERN**: Uses CHILD flow ID from URL (AssessmentFlow.id)

    Args:
        flow_id: Child flow UUID from URL path
        current_user: Authenticated user
        db: Database session
        context: Request context with tenant IDs

    Returns:
        Dict with:
        - flow_id: Child flow ID (user-facing)
        - app_server_dependencies: List of app→server dependencies
        - app_app_dependencies: List of app→app dependencies
        - applications: Metadata for all selected applications
        - agent_results: Phase analysis from agent (if executed)

    Raises:
        HTTPException 404: Flow not found
        HTTPException 500: Analysis retrieval failed
    """
    try:
        # ============================================
        # STEP 1: Query with master_flow_id fallback (MFO two-table pattern)
        # URL may receive master_flow_id or child id - support both
        # ============================================
        stmt = select(AssessmentFlow).where(
            sa.or_(
                AssessmentFlow.master_flow_id == UUID(flow_id),
                AssessmentFlow.id == UUID(flow_id),
            ),
            AssessmentFlow.client_account_id == context.client_account_id,
            AssessmentFlow.engagement_id == context.engagement_id,
        )
        result = await db.execute(stmt)
        child_flow = result.scalar_one_or_none()

        # Validate flow exists
        if not child_flow:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Get selected application IDs (filter dependencies by these)
        selected_app_ids = child_flow.selected_application_ids or []
        if not selected_app_ids:
            # No applications selected, return empty graph
            return build_empty_dependency_response(flow_id)

        # ============================================
        # STEP 2: Get dependencies filtered by selected applications
        # ============================================
        dependency_repo = DependencyRepository(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
        )

        # Get ALL dependencies (server, database, network, application, etc.)
        all_deps = await dependency_repo.get_all_dependencies_for_flow(
            engagement_id=str(context.engagement_id),
            application_ids=[UUID(app_id) for app_id in selected_app_ids],
        )

        # Get application metadata for graph nodes
        applications_metadata = await dependency_repo.get_available_applications()
        # Filter to only selected applications
        filtered_apps = [
            app for app in applications_metadata if app["id"] in selected_app_ids
        ]

        # Populate dependencies field on applications (frontend expects comma-separated IDs)
        populate_application_dependencies(filtered_apps, all_deps)

        # Construct dependency graph from raw data
        dependency_graph = build_dependency_graph(filtered_apps, all_deps)

        # Extract agent results from phase_results (if executed)
        agent_results = None
        if (
            child_flow.phase_results
            and "dependency_analysis" in child_flow.phase_results
        ):
            agent_results = child_flow.phase_results["dependency_analysis"]

        logger.info(
            safe_log_format(
                "Retrieved dependency analysis: flow_id={flow_id}, "
                "app_count={app_count}, total_deps={total_deps}",
                flow_id=flow_id,
                app_count=len(filtered_apps),
                total_deps=len(all_deps),
            )
        )

        return {
            "flow_id": flow_id,  # Return child ID (user expects this)
            "all_dependencies": all_deps,  # Unified dependencies (all types)
            "app_server_dependencies": [],  # Deprecated - kept for backward compatibility
            "app_app_dependencies": [],  # Deprecated - kept for backward compatibility
            "applications": filtered_apps,
            "dependency_graph": dependency_graph,  # Structured graph for visualization
            "agent_results": agent_results,
            "metadata": {
                "total_applications": len(filtered_apps),
                "total_dependencies": len(all_deps),
                "analysis_executed": agent_results is not None,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to get dependency analysis: {str_e}", str_e=str(e))
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve dependency analysis"
        )


@router.post("/{flow_id}/dependency/execute")
async def execute_dependency_analysis(
    flow_id: str,  # ← CHILD flow ID from URL
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Manually execute dependency analysis phase for assessment flow.

    This endpoint allows manual re-execution of the dependency_analysis phase:
    - When the phase hasn't been run yet
    - When the phase failed and needs to be retried
    - When the user wants to refresh the analysis with updated data

    **CRITICAL PATTERN**: Uses CHILD flow ID from URL, resolves to MASTER flow ID for MFO

    Args:
        flow_id: Child flow UUID from URL path
        current_user: Authenticated user
        db: Database session
        context: Request context with tenant IDs

    Returns:
        Dict with:
        - flow_id: Child flow ID (user-facing)
        - phase: Phase name that was executed
        - status: Execution status (started/running/completed/failed)
        - message: User-facing status message

    Raises:
        HTTPException 404: Flow not found
        HTTPException 500: Phase execution failed
    """
    try:
        # ============================================
        # STEP 1: Query with master_flow_id fallback (MFO two-table pattern)
        # URL may receive master_flow_id or child id - support both
        # ============================================
        stmt = select(AssessmentFlow).where(
            sa.or_(
                AssessmentFlow.master_flow_id == UUID(flow_id),
                AssessmentFlow.id == UUID(flow_id),
            ),
            AssessmentFlow.client_account_id == context.client_account_id,
            AssessmentFlow.engagement_id == context.engagement_id,
        )
        result = await db.execute(stmt)
        child_flow = result.scalar_one_or_none()

        # Validate flow exists
        if not child_flow:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Validate master flow ID exists
        if not child_flow.master_flow_id:
            raise HTTPException(
                status_code=500,
                detail="Assessment flow not integrated with MFO (missing master_flow_id)",
            )

        # ============================================
        # STEP 2: Execute phase via MFO using MASTER flow ID
        # ============================================
        from app.services.master_flow_orchestrator import MasterFlowOrchestrator

        orchestrator = MasterFlowOrchestrator(db, context)

        # Execute dependency_analysis phase with child flow ID in phase_input
        phase_result = await orchestrator.execute_phase(
            str(child_flow.master_flow_id),  # ← MASTER flow ID (MFO routing)
            "dependency_analysis",
            phase_input={
                "flow_id": flow_id,  # ← CHILD flow ID (for persistence)
                "selected_application_ids": child_flow.selected_application_ids or [],
            },
        )

        logger.info(
            safe_log_format(
                "Executed dependency_analysis phase: flow_id={flow_id}, status={status}",
                flow_id=flow_id,
                status=phase_result.get("status"),
            )
        )

        return {
            "flow_id": flow_id,  # Return child ID (user expects this)
            "phase": "dependency_analysis",
            "status": phase_result.get("status", "started"),
            "message": "Dependency analysis execution started",
            "result": phase_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to execute dependency analysis: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to execute dependency analysis: {str(e)}"
        )


@router.put("/{flow_id}/dependency/update")
async def update_application_dependencies(
    flow_id: str,  # ← CHILD flow ID from URL
    request: UpdateDependenciesRequest = Body(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Update dependencies for an application in the assessment flow.

    This endpoint allows users to manually manage application dependencies
    via the AG Grid dependency management table.

    **CRITICAL**: Uses request body per API_REQUEST_PATTERNS.md
    - POST/PUT/DELETE endpoints MUST use request body
    - NOT query parameters

    Args:
        flow_id: Child flow UUID from URL path
        request: Request body with application_id and dependencies
        current_user: Authenticated user
        db: Database session
        context: Request context with tenant IDs

    Returns:
        Dict with:
        - success: Boolean indicating update success
        - application_id: Application ID that was updated
        - dependencies_count: Number of dependencies set

    Raises:
        HTTPException 404: Flow or application not found
        HTTPException 500: Update failed
    """
    try:
        # Validate flow exists with master_flow_id fallback (MFO two-table pattern)
        stmt = select(AssessmentFlow).where(
            sa.or_(
                AssessmentFlow.master_flow_id == UUID(flow_id),
                AssessmentFlow.id == UUID(flow_id),
            ),
            AssessmentFlow.client_account_id == context.client_account_id,
            AssessmentFlow.engagement_id == context.engagement_id,
        )
        result = await db.execute(stmt)
        child_flow = result.scalar_one_or_none()

        if not child_flow:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Parse dependency IDs from request
        dependency_ids = []
        if request.dependencies:
            dependency_ids = [
                dep.strip() for dep in request.dependencies.split(",") if dep.strip()
            ]

        # Update dependencies using DependencyRepository
        dependency_repo = DependencyRepository(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
        )

        # Clear existing dependencies for this application to prevent duplicates
        await dependency_repo.delete_dependencies_for_application(
            application_id=request.application_id
        )

        logger.info(
            safe_log_format(
                "Cleared existing dependencies for application update: app_id={app_id}",
                app_id=request.application_id,
            )
        )

        # Create new dependencies (bulk operation for performance)
        await dependency_repo.bulk_create_dependencies(
            source_asset_id=request.application_id,
            target_asset_ids=dependency_ids,
            dependency_type="manual",  # Mark as manually created
            confidence_score=1.0,  # Manual dependencies have 100% confidence
        )

        await db.commit()

        logger.info(
            safe_log_format(
                "Updated dependencies for application: app_id={app_id}, count={count}",
                app_id=request.application_id,
                count=len(dependency_ids),
            )
        )

        return {
            "success": True,
            "application_id": request.application_id,
            "dependencies_count": len(dependency_ids),
            "message": f"Updated {len(dependency_ids)} dependencies for application",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Failed to update dependencies: {str_e}", str_e=str(e))
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to update dependencies: {str(e)}"
        )
