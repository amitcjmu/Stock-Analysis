"""
Dependency Analysis API Endpoints

This module contains all dependency analysis related endpoints,
extracted from unified_discovery.py for better modularity.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.logging import safe_log_format
from app.models.discovery_flow import DiscoveryFlow
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


class DependencyAnalysisRequest(BaseModel):
    """Request model for dependency analysis"""

    analysis_type: str = "app-server"
    configuration: Optional[dict] = None


@router.get("/analysis")
async def get_dependency_analysis(
    flow_id: str = Query(None, description="Flow ID for dependency analysis"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get dependency analysis results."""
    try:
        logger.info(
            safe_log_format(
                "Getting dependency analysis for flow: {flow_id}", flow_id=flow_id
            )
        )

        if flow_id:
            # Get specific flow's dependency analysis
            stmt = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id == flow_id,
                    DiscoveryFlow.client_account_id == context.client_account_id,
                    DiscoveryFlow.engagement_id == context.engagement_id,
                )
            )
            result = await db.execute(stmt)
            flow = result.scalar_one_or_none()

            if flow:
                dependencies = flow.dependencies or {}
            else:
                dependencies = {}
        else:
            # Return generic dependency structure
            dependencies = {
                "total_dependencies": 0,
                "dependency_quality": {"quality_score": 0},
                "cross_application_mapping": {
                    "cross_app_dependencies": [],
                    "application_clusters": [],
                    "dependency_graph": {"nodes": [], "edges": []},
                },
                "impact_analysis": {"impact_summary": {}},
            }

        return {"success": True, "data": {"dependency_analysis": dependencies}}

    except Exception as e:
        logger.error(safe_log_format("Failed to get dependency analysis: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_dependencies(
    request: DependencyAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Create dependency analysis through Master Flow Orchestrator."""
    try:
        logger.info(
            safe_log_format(
                "Creating dependency analysis: {request_analysis_type}",
                request_analysis_type=request.analysis_type,
            )
        )

        # Create a new discovery flow for dependency analysis
        orchestrator = MasterFlowOrchestrator(db, context)
        flow_id, flow_details = await orchestrator.create_flow(
            "discovery",
            f"Dependency Analysis - {request.analysis_type}",
            {
                "analysis_type": request.analysis_type,
                "focus": "dependency_analysis",
                **(request.configuration or {}),
            },
            {"analysis_request": request.dict()},
        )

        return {
            "success": True,
            "flow_id": str(flow_id),
            "analysis_type": request.analysis_type,
            "result": flow_details,
            "message": "Dependency analysis created successfully",
        }

    except Exception as e:
        logger.error(safe_log_format("Failed to create dependency analysis: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications")
async def get_available_applications(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get available applications for dependency analysis."""
    try:
        logger.info("Getting available applications")

        # Get applications from discovery flows in this engagement
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flows = result.scalars().all()

        applications = []
        for flow in flows:
            if flow.discovered_assets:
                assets = flow.discovered_assets.get("applications", [])
                applications.extend(assets)

        return {
            "success": True,
            "applications": applications,
            "count": len(applications),
        }

    except Exception as e:
        logger.error(safe_log_format("Failed to get available applications: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers")
async def get_available_servers(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get available servers for dependency analysis."""
    try:
        logger.info("Getting available servers")

        # Get servers from discovery flows in this engagement
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flows = result.scalars().all()

        servers = []
        for flow in flows:
            if flow.discovered_assets:
                assets = flow.discovered_assets.get("servers", [])
                servers.extend(assets)

        return {"success": True, "servers": servers, "count": len(servers)}

    except Exception as e:
        logger.error(safe_log_format("Failed to get available servers: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/{analysis_type}")
async def analyze_dependencies(
    analysis_type: str,
    request: Optional[DependencyAnalysisRequest] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Analyze dependencies of a specific type."""
    try:
        logger.info(
            safe_log_format(
                "Analyzing dependencies: {analysis_type}", analysis_type=analysis_type
            )
        )

        # Create a new discovery flow focused on dependency analysis
        orchestrator = MasterFlowOrchestrator(db, context)
        flow_id, flow_details = await orchestrator.create_flow(
            "discovery",
            f"Dependency Analysis - {analysis_type}",
            {
                "analysis_type": analysis_type,
                "focus": "dependency_analysis",
                "auto_execute": True,
                **(request.configuration if request else {}),
            },
            {
                "analysis_request": {
                    "analysis_type": analysis_type,
                    "configuration": (request.configuration if request else {}),
                }
            },
        )

        # Execute the dependency analysis phase
        analysis_result = await orchestrator.execute_phase(
            str(flow_id), "dependency_analysis", {"analysis_type": analysis_type}
        )

        return {
            "success": True,
            "flow_id": str(flow_id),
            "analysis_type": analysis_type,
            "result": analysis_result,
            "message": f"Dependency analysis '{analysis_type}' completed successfully",
        }

    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to analyze dependencies {analysis_type}: {e}",
                analysis_type=analysis_type,
                e=e,
            )
        )
        raise HTTPException(status_code=500, detail=str(e))
