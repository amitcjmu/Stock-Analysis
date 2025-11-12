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
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
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
            return {
                "flow_id": flow_id,
                "app_server_dependencies": [],
                "app_app_dependencies": [],
                "applications": [],
                "agent_results": None,
                "message": "No applications selected for assessment",
            }

        # ============================================
        # STEP 2: Get dependencies filtered by selected applications
        # ============================================
        dependency_repo = DependencyRepository(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
        )

        # Get application-to-server dependencies
        app_server_deps = await dependency_repo.get_app_server_dependencies_for_flow(
            engagement_id=str(context.engagement_id),
            application_ids=[UUID(app_id) for app_id in selected_app_ids],
        )

        # Get application-to-application dependencies
        app_app_deps = await dependency_repo.get_app_app_dependencies_for_flow(
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
                "app_count={app_count}, server_deps={server_count}, app_deps={app_count_deps}",
                flow_id=flow_id,
                app_count=len(filtered_apps),
                server_count=len(app_server_deps),
                app_count_deps=len(app_app_deps),
            )
        )

        return {
            "flow_id": flow_id,  # Return child ID (user expects this)
            "app_server_dependencies": app_server_deps,
            "app_app_dependencies": app_app_deps,
            "applications": filtered_apps,
            "agent_results": agent_results,
            "metadata": {
                "total_applications": len(filtered_apps),
                "total_dependencies": len(app_server_deps) + len(app_app_deps),
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


# NOTE: Manual execution endpoint removed per design - dependency_analysis
# auto-executes via MFO when navigating from complexity page.
# The MFO handles phase progression automatically when user clicks "Continue"
# from the complexity page, executing dependency_analysis before navigation.


# ============================================
# VALIDATION CHECKLIST
# ============================================
# Before committing, verify:
# [x] URL receives child flow ID (from user)
# [x] Query uses AssessmentFlow.id (primary key, not flow_id)
# [x] Extracted master_flow_id from child_flow.master_flow_id
# [x] Passed master_flow_id to execute_phase_command()
# [x] Included child flow_id in phase_input dict
# [x] Returned child flow_id to user (not master_flow_id)
# [x] Used get_current_context_dependency (not get_current_context)
# [x] Added try/except for HTTPException passthrough
# [x] Applied multi-tenant scoping (client_account_id, engagement_id)
