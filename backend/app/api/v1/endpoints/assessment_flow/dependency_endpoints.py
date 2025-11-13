"""
Dependency analysis endpoints for assessment flows.
Handles dependency graph retrieval and analysis execution via MFO.
Uses MFO integration layer per ADR-006 (Master Flow Orchestrator pattern).

CRITICAL: Follows MFO Flow ID Pattern from mfo_two_table_flow_id_pattern_critical.md
- URL receives CHILD flow ID (AssessmentFlow.id)
- MFO expects MASTER flow ID (extracted from child.master_flow_id)
- phase_input includes CHILD flow ID for persistence
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format
from app.models.assessment_flow import AssessmentFlow
from app.repositories.dependency_repository import DependencyRepository

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class UpdateDependenciesRequest(BaseModel):
    """Request model for updating application dependencies."""

    application_id: str
    dependencies: Optional[str] = None  # Comma-separated asset IDs, None to clear


# =============================================================================
# Helper Functions (Complexity Reduction)
# =============================================================================


def _build_empty_dependency_response(flow_id: str) -> Dict[str, Any]:
    """
    Build empty dependency response when no applications are selected.

    Args:
        flow_id: Child flow UUID

    Returns:
        Dict with empty graph structure
    """
    return {
        "flow_id": flow_id,
        "app_server_dependencies": [],
        "app_app_dependencies": [],
        "applications": [],
        "dependency_graph": {
            "nodes": [],
            "edges": [],
            "metadata": {
                "dependency_count": 0,
                "node_count": 0,
                "app_count": 0,
                "server_count": 0,
            },
        },
        "agent_results": None,
        "message": "No applications selected for assessment",
    }


def _populate_application_dependencies(
    filtered_apps: list[Dict[str, Any]], all_deps: list[Dict[str, Any]]
) -> None:
    """
    Populate dependencies field on applications for frontend table display.

    Modifies filtered_apps in-place to add:
    - dependencies: Comma-separated string of dependency IDs
    - dependency_names: Comma-separated string of dependency names

    Args:
        filtered_apps: List of application metadata dicts (modified in-place)
        all_deps: List of all dependency records
    """
    for app in filtered_apps:
        app_id = app["id"]
        dep_ids = []
        dep_names = []

        # Collect ALL dependencies (server, database, application, network, etc.)
        for dep in all_deps:
            if dep.get("source_app_id") == app_id:
                target_info = dep.get("target_info", {})
                target_id = target_info.get("id")
                target_name = target_info.get("name")
                if target_id:
                    dep_ids.append(target_id)
                    if target_name:
                        dep_names.append(target_name)

        # Set dependencies as comma-separated string (or None if no deps)
        app["dependencies"] = ",".join([str(d) for d in dep_ids]) if dep_ids else None
        # Add dependency_names for display in frontend table
        app["dependency_names"] = ",".join(dep_names) if dep_names else None


def _build_dependency_graph(
    filtered_apps: list[Dict[str, Any]], all_deps: list[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Construct dependency graph from application and dependency data.

    Builds graph structure with nodes (applications, servers, databases, etc.)
    and edges (dependencies between assets).

    Args:
        filtered_apps: List of selected application metadata
        all_deps: List of all dependency records

    Returns:
        Dict with:
        - nodes: List of graph nodes with type, name, metadata
        - edges: List of directed edges (source -> target)
        - metadata: Graph statistics (counts)
    """
    nodes = []
    edges = []
    node_ids = set()

    # Add source application nodes from filtered_apps
    for app in filtered_apps:
        app_id = app["id"]
        if app_id not in node_ids:
            nodes.append(
                {
                    "id": app_id,
                    "name": app.get("application_name") or app.get("name"),
                    "type": "application",
                    "business_criticality": app.get("business_criticality"),
                }
            )
            node_ids.add(app_id)

    # Add source application nodes from dependencies (in case not in filtered_apps)
    for dep in all_deps:
        source_id = dep.get("source_app_id")
        if source_id and source_id not in node_ids:
            nodes.append(
                {
                    "id": source_id,
                    "name": dep.get("source_app_name"),
                    "type": "application",
                }
            )
            node_ids.add(source_id)

    # Add target asset nodes and edges from all_deps (unified query)
    for dep in all_deps:
        target_info = dep.get("target_info", {})
        target_id = target_info.get("id")
        target_type = target_info.get("type", "unknown")

        # Add target node if not already present
        if target_id and target_id not in node_ids:
            node_data = {
                "id": target_id,
                "name": target_info.get("name"),
                "type": target_type,
            }

            # Add type-specific fields
            if target_type == "server":
                node_data["hostname"] = target_info.get("hostname")
            elif target_type in ("application", "database"):
                node_data["application_name"] = target_info.get("application_name")

            nodes.append(node_data)
            node_ids.add(target_id)

        # Add edge
        edges.append(
            {
                "source": dep.get("source_app_id"),
                "target": target_id,
                "type": dep.get("dependency_type", "unknown"),
                "source_name": dep.get("source_app_name"),
                "target_name": target_info.get("name"),
            }
        )

    # Count node types
    app_count = sum(1 for n in nodes if n["type"] == "application")
    server_count = sum(1 for n in nodes if n["type"] == "server")

    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "dependency_count": len(edges),
            "node_count": len(nodes),
            "app_count": app_count,
            "server_count": server_count,
        },
    }


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
        # STEP 1: Query child flow table using CHILD ID
        # ============================================
        stmt = select(AssessmentFlow).where(
            and_(
                AssessmentFlow.id == UUID(flow_id),  # ← PRIMARY KEY (child ID)
                AssessmentFlow.client_account_id == context.client_account_id,
                AssessmentFlow.engagement_id == context.engagement_id,
            )
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
            return _build_empty_dependency_response(flow_id)

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

        # ============================================
        # STEP 2.5: Populate dependencies field on applications
        # ============================================
        # The frontend table expects app.dependencies to be a comma-separated string
        # of dependency IDs. Also add dependency_names for display.
        _populate_application_dependencies(filtered_apps, all_deps)

        # ============================================
        # STEP 3: Construct dependency graph from raw data
        # ============================================
        dependency_graph = _build_dependency_graph(filtered_apps, all_deps)

        # ============================================
        # STEP 3: Extract agent results from phase_results (if executed)
        # ============================================
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
        # STEP 1: Query child flow table using CHILD ID
        # ============================================
        stmt = select(AssessmentFlow).where(
            and_(
                AssessmentFlow.id == UUID(flow_id),  # ← PRIMARY KEY (child ID)
                AssessmentFlow.client_account_id == context.client_account_id,
                AssessmentFlow.engagement_id == context.engagement_id,
            )
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
        # Validate flow exists
        stmt = select(AssessmentFlow).where(
            and_(
                AssessmentFlow.id == UUID(flow_id),
                AssessmentFlow.client_account_id == context.client_account_id,
                AssessmentFlow.engagement_id == context.engagement_id,
            )
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
