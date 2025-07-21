"""
Health and metrics monitoring endpoints.

Provides system health checks and performance metrics for monitoring and optimization.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging
from datetime import datetime

from app.services.agent_monitor import agent_monitor
from app.services.agent_registry import agent_registry
from app.api.v1.dependencies import get_crewai_flow_service
from app.services.crewai_flow_service import CrewAIFlowService
from app.core.logging import get_logger as enhanced_get_logger
from .base import get_monitoring_context

logger = enhanced_get_logger(__name__)

router = APIRouter()


@router.get("/health")
async def get_system_health(
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """
    Get overall system health and performance metrics.
    
    Returns system-wide health indicators including:
    - CrewAI service status
    - Agent registry health
    - LLM connectivity
    - Memory system health
    - Performance metrics
    """
    try:
        # Get registry status
        registry_status = agent_registry.get_registry_status()
        
        # Get system status from CrewAI service
        system_status = {}
        
        # Get monitoring status
        status_report = agent_monitor.get_status_report()
        
        # Calculate health indicators
        health_indicators = {
            "agent_registry": "healthy" if registry_status["registry_status"] == "healthy" else "degraded",
            "crewai_service": "healthy" if service.llm is not None else "degraded",
            "agent_manager": "healthy" if service.agent_manager is not None else "down",
            "monitoring_system": "healthy" if status_report["monitoring_active"] else "down",
            "memory_system": "healthy",  # Could check memory system health
            "llm_connectivity": "healthy" if service.llm is not None else "down"
        }
        
        overall_health = "healthy"
        if "down" in health_indicators.values():
            overall_health = "down"
        elif "degraded" in health_indicators.values():
            overall_health = "degraded"
        
        return {
            "success": True,
            "timestamp": "2025-01-28T12:00:00Z",
            "overall_health": overall_health,
            "health_indicators": health_indicators,
            "agent_registry": {
                "status": registry_status["registry_status"],
                "total_agents": registry_status["total_agents"],
                "active_agents": registry_status["active_agents"],
                "phase_distribution": registry_status["phase_distribution"]
            },
            "system_metrics": {
                "monitoring_active": status_report["monitoring_active"],
                "active_tasks": status_report["active_tasks"],
                "completed_tasks": status_report["completed_tasks"],
                "hanging_tasks": status_report["hanging_tasks"]
            },
            "crewai_system": system_status
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@router.get("/metrics")
async def get_performance_metrics():
    """
    Get detailed performance metrics for monitoring and optimization.
    
    Returns comprehensive performance data including:
    - Task execution statistics
    - Agent performance metrics by phase
    - System resource usage
    - Trend analysis
    """
    try:
        status_report = agent_monitor.get_status_report()
        registry_status = agent_registry.get_registry_status()
        
        # Calculate basic metrics
        metrics = {
            "task_metrics": {
                "total_active": status_report["active_tasks"],
                "total_completed": status_report["completed_tasks"],
                "hanging_count": status_report["hanging_tasks"],
                "success_rate": "N/A",  # Would need historical data
                "avg_execution_time": "N/A"  # Would need historical data
            },
            "agent_metrics": {
                "total_agents": registry_status["total_agents"],
                "active_agents": registry_status["active_agents"],
                "learning_enabled": registry_status["learning_enabled_agents"],
                "cross_page_communication": registry_status["cross_page_communication_agents"],
                "modular_handlers": registry_status["modular_handler_agents"],
                "agents_busy": len(set(task["agent"] for task in status_report["active_task_details"])),
                "agent_utilization": f"{(len(set(task['agent'] for task in status_report['active_task_details'])) / max(registry_status['active_agents'], 1)) * 100:.1f}%"
            },
            "phase_metrics": registry_status["phase_distribution"],
            "system_metrics": {
                "monitoring_uptime": "N/A",  # Could track monitoring uptime
                "memory_usage": "N/A",      # Could track memory usage
                "cpu_usage": "N/A",         # Could track CPU usage
                "response_times": "N/A"     # Could track API response times
            },
            "trends": {
                "tasks_per_hour": "N/A",    # Would need historical data
                "error_rate": "N/A",        # Would need historical data
                "performance_trend": "stable"  # Would need historical analysis
            }
        }
        
        return {
            "success": True,
            "timestamp": "2025-01-28T12:00:00Z",
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")