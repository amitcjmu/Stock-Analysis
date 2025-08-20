"""
Status handler for discovery agent.

This module contains the status-related endpoints for the discovery agent.
Simplified version with modularized components.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.services.discovery_flow_service import DiscoveryFlowService

# Import modularized components
from .status_services import get_crewai_flow_service
from .status_insights import _get_dynamic_agent_insights, _get_cached_agent_insights
from .status_data import _get_data_classifications, get_asset_count_by_status

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
async def get_discovery_status(
    db: AsyncSession = Depends(get_db), context: dict = Depends(get_current_context)
):
    """
    Get comprehensive discovery status using V2 Discovery Flow architecture.
    Replaces legacy session-based status checks.
    """
    try:
        logger.info("🔍 Getting discovery status using V2 Discovery Flow")

        # Initialize V2 services
        flow_repo = DiscoveryFlowRepository(
            db, context.get("client_account_id"), user_id=context.get("user_id")
        )
        flow_service = DiscoveryFlowService(flow_repo)

        # Get all active discovery flows for this client
        active_flows = await flow_service.get_active_flows()

        # Get flow statistics
        flow_stats = await flow_service.get_flow_statistics()

        return {
            "success": True,
            "data": {
                "active_flows": len(active_flows),
                "total_flows": flow_stats.get("total_flows", 0),
                "completed_flows": flow_stats.get("completed_flows", 0),
                "in_progress_flows": flow_stats.get("in_progress_flows", 0),
                "agent_status": "active",  # Simplified agent status
                "flows": [
                    {
                        "flow_id": flow.flow_id,
                        "current_phase": flow.current_phase,
                        "progress_percentage": flow.progress_percentage,
                        "status": flow.status,
                        "created_at": (
                            flow.created_at.isoformat() if flow.created_at else None
                        ),
                        "updated_at": (
                            flow.updated_at.isoformat() if flow.updated_at else None
                        ),
                    }
                    for flow in active_flows
                ],
            },
        }

    except Exception as e:
        logger.error(safe_log_format("Error getting V2 discovery status: {e}", e=e))
        return {
            "success": False,
            "error": "Failed to retrieve discovery status",
            "data": {
                "active_flows": 0,
                "total_flows": 0,
                "completed_flows": 0,
                "in_progress_flows": 0,
                "agent_status": "unavailable",
                "flows": [],
            },
        }


@router.get("/health")
async def agent_discovery_health():
    """Simple health check for discovery agent."""
    return {
        "status": "healthy",
        "agent": "discovery",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/monitor")
async def get_agent_monitor(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Get enhanced agent monitor data with dynamic insights.

    Returns real-time insights based on actual imported data and analysis.
    Optimized for the AgentMonitor React component with AgentInsightsSection support.
    """
    try:
        logger.info("🚀 Getting enhanced agent monitor data with dynamic insights")

        # Get dynamic agent insights based on actual data
        agent_insights = await _get_dynamic_agent_insights(db, context)

        # Get data classifications
        data_classifications = await _get_data_classifications(db, context)

        # Get asset counts by status
        asset_counts = await get_asset_count_by_status(db, context)

        # Structure for frontend AgentMonitor component
        monitor_data = {
            "agent_status": "active",
            "last_activity": datetime.utcnow().isoformat(),
            "insights": agent_insights,
            "classifications": data_classifications,
            "statistics": {
                "total_insights": len(agent_insights),
                "high_priority_insights": len(
                    [i for i in agent_insights if i.get("priority") == "high"]
                ),
                "actionable_insights": len(
                    [i for i in agent_insights if i.get("actionable", False)]
                ),
                "asset_counts": asset_counts,
            },
            "system_health": {
                "discovery_service": "operational",
                "database": "connected",
                "data_analysis": "active" if agent_insights else "idle",
            },
        }

        return {
            "success": True,
            "data": monitor_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(safe_log_format("Error in enhanced agent monitor: {e}", e=e))

        # Return cached fallback insights
        cached_insights = _get_cached_agent_insights()

        return {
            "success": False,
            "error": {
                "code": "SERVICE_DEGRADED",
                "message": "Service degraded; returning fallback data",
            },
            "data": {
                "agent_status": "degraded",
                "last_activity": datetime.utcnow().isoformat(),
                "insights": cached_insights,
                "classifications": [],
                "statistics": {
                    "total_insights": len(cached_insights),
                    "high_priority_insights": 0,
                    "actionable_insights": len(cached_insights),
                    "asset_counts": {"discovered": 0, "pending": 0, "classified": 0},
                },
                "system_health": {
                    "discovery_service": "degraded",
                    "database": "checking",
                    "data_analysis": "fallback",
                },
            },
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Using cached fallback data due to service unavailability",
        }


@router.get("/agent-status")
async def get_agent_status(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    flow_service: DiscoveryFlowService = Depends(get_crewai_flow_service),
):
    """
    Get comprehensive agent status information.

    Combines discovery flow status, agent insights, and system health
    to provide a complete view of the discovery agent's current state.
    """
    try:
        logger.info("📊 Getting comprehensive agent status information")

        # Get active flows
        active_flows = await flow_service.get_active_flows()

        # Get agent insights
        insights = await _get_dynamic_agent_insights(db, context)

        # Get data classifications
        classifications = await _get_data_classifications(db, context)

        # Calculate agent performance metrics
        performance_metrics = {
            "active_flows": len(active_flows),
            "total_insights": len(insights),
            "high_confidence_insights": len(
                [i for i in insights if i.get("confidence") == "high"]
            ),
            "actionable_items": len(
                [i for i in insights if i.get("actionable", False)]
            ),
            "classification_coverage": len(classifications),
        }

        # Determine overall agent status
        overall_status = "healthy"
        if performance_metrics["active_flows"] == 0:
            overall_status = "idle"
        elif performance_metrics["actionable_items"] > 5:
            overall_status = "busy"

        return {
            "success": True,
            "agent_status": {
                "overall_status": overall_status,
                "service_health": "operational",
                "last_update": datetime.utcnow().isoformat(),
                "performance": performance_metrics,
                "capabilities": {
                    "discovery_flows": True,
                    "data_analysis": True,
                    "insight_generation": True,
                    "classification": True,
                },
            },
            "active_processes": {
                "flows": [
                    {
                        "id": flow.flow_id,
                        "phase": flow.current_phase,
                        "progress": flow.progress_percentage,
                        "status": flow.status,
                    }
                    for flow in active_flows
                ],
                "insights": insights[:3],  # Return top 3 insights
                "classifications": classifications[:3],  # Return top 3 classifications
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(safe_log_format("Error getting agent status: {e}", e=e))
        return {
            "success": False,
            "error": "Failed to retrieve agent status",
            "agent_status": {
                "overall_status": "error",
                "service_health": "degraded",
                "last_update": datetime.utcnow().isoformat(),
                "performance": {"active_flows": 0, "total_insights": 0},
                "capabilities": {"discovery_flows": False},
            },
            "active_processes": {"flows": [], "insights": [], "classifications": []},
            "timestamp": datetime.utcnow().isoformat(),
        }
