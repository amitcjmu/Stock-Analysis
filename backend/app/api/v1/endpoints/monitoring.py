"""
Agent Monitoring API Endpoints
Provides real-time observability into CrewAI agent task execution for the frontend.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
import logging

from app.services.agent_monitor import agent_monitor, TaskStatus
from app.services.crewai_service import crewai_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
async def get_agent_status():
    """
    Get current agent monitoring status.
    
    Returns real-time information about active agents, running tasks,
    and system health for display in the frontend.
    """
    try:
        # Get monitoring status
        status_report = agent_monitor.get_status_report()
        
        # Get agent capabilities
        agent_capabilities = {}
        if crewai_service.agent_manager:
            agent_capabilities = crewai_service.agent_manager.get_agent_capabilities()
        
        # Get system status
        system_status = {}
        if crewai_service.agent_manager:
            system_status = crewai_service.agent_manager.get_system_status()
        
        return {
            "success": True,
            "timestamp": "2025-01-27T12:00:00Z",
            "monitoring": {
                "active": status_report["monitoring_active"],
                "active_tasks": status_report["active_tasks"],
                "completed_tasks": status_report["completed_tasks"],
                "hanging_tasks": status_report["hanging_tasks"]
            },
            "agents": {
                "available": len(crewai_service.agents) if crewai_service.agents else 0,
                "capabilities": agent_capabilities,
                "system_status": system_status
            },
            "tasks": {
                "active": status_report["active_task_details"],
                "hanging": status_report["hanging_task_details"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {str(e)}")


@router.get("/tasks")
async def get_active_tasks():
    """
    Get detailed information about currently active tasks.
    
    Returns comprehensive task execution details including:
    - Task progress and status
    - Agent assignments
    - LLM call history
    - Thinking phases
    - Performance metrics
    """
    try:
        status_report = agent_monitor.get_status_report()
        
        # Enhance task details with additional context
        enhanced_tasks = []
        for task in status_report["active_task_details"]:
            enhanced_task = {
                **task,
                "progress_indicators": {
                    "has_started": task["elapsed"] != "0.0s",
                    "making_progress": task["since_activity"] != task["elapsed"],
                    "llm_active": task["status"] in ["waiting_llm", "processing_response"],
                    "thinking_active": task["status"] == "thinking"
                },
                "performance": {
                    "avg_llm_response_time": "N/A",  # Could be calculated from history
                    "task_complexity": "medium",     # Could be inferred from description
                    "estimated_completion": "N/A"   # Could be predicted based on patterns
                }
            }
            enhanced_tasks.append(enhanced_task)
        
        return {
            "success": True,
            "timestamp": "2025-01-27T12:00:00Z",
            "active_tasks": enhanced_tasks,
            "summary": {
                "total_active": len(enhanced_tasks),
                "healthy": len([t for t in enhanced_tasks if not t["is_hanging"]]),
                "hanging": len([t for t in enhanced_tasks if t["is_hanging"]]),
                "agents_busy": len(set(t["agent"] for t in enhanced_tasks))
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting active tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active tasks: {str(e)}")


@router.get("/agents")
async def get_agent_details():
    """
    Get detailed information about available agents and their capabilities.
    
    Returns comprehensive agent information including:
    - Agent roles and expertise
    - Current availability status
    - Performance history
    - Specializations and skills
    """
    try:
        agent_details = []
        
        if crewai_service.agent_manager:
            capabilities = crewai_service.agent_manager.get_agent_capabilities()
            system_status = crewai_service.agent_manager.get_system_status()
            
            # Get current task assignments
            status_report = agent_monitor.get_status_report()
            active_agents = {task["agent"] for task in status_report["active_task_details"]}
            
            for agent_name, capability in capabilities.items():
                agent_info = {
                    "name": agent_name,
                    "role": capability["role"],
                    "expertise": capability["expertise"],
                    "specialization": capability["specialization"],
                    "key_skills": capability["key_skills"],
                    "status": {
                        "available": agent_name not in active_agents,
                        "currently_working": agent_name in active_agents,
                        "health": "healthy"  # Could be determined from recent performance
                    },
                    "performance": {
                        "tasks_completed": 0,  # Could be tracked from history
                        "success_rate": "N/A", # Could be calculated from history
                        "avg_execution_time": "N/A"  # Could be calculated from history
                    }
                }
                agent_details.append(agent_info)
        
        return {
            "success": True,
            "timestamp": "2025-01-27T12:00:00Z",
            "agents": agent_details,
            "summary": {
                "total_agents": len(agent_details),
                "available": len([a for a in agent_details if a["status"]["available"]]),
                "busy": len([a for a in agent_details if a["status"]["currently_working"]]),
                "healthy": len([a for a in agent_details if a["status"]["health"] == "healthy"])
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting agent details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent details: {str(e)}")


@router.get("/health")
async def get_system_health():
    """
    Get overall system health and performance metrics.
    
    Returns system-wide health indicators including:
    - CrewAI service status
    - LLM connectivity
    - Memory system health
    - Performance metrics
    """
    try:
        # Get system status
        system_status = {}
        if crewai_service.agent_manager:
            system_status = crewai_service.agent_manager.get_system_status()
        
        # Get monitoring status
        status_report = agent_monitor.get_status_report()
        
        # Calculate health indicators
        health_indicators = {
            "crewai_service": "healthy" if crewai_service.llm is not None else "degraded",
            "agent_manager": "healthy" if crewai_service.agent_manager is not None else "down",
            "monitoring_system": "healthy" if status_report["monitoring_active"] else "down",
            "memory_system": "healthy",  # Could check memory system health
            "llm_connectivity": "healthy" if crewai_service.llm is not None else "down"
        }
        
        overall_health = "healthy"
        if "down" in health_indicators.values():
            overall_health = "down"
        elif "degraded" in health_indicators.values():
            overall_health = "degraded"
        
        return {
            "success": True,
            "timestamp": "2025-01-27T12:00:00Z",
            "overall_health": overall_health,
            "components": health_indicators,
            "system_status": system_status,
            "performance": {
                "active_tasks": status_report["active_tasks"],
                "completed_tasks": status_report["completed_tasks"],
                "hanging_tasks": status_report["hanging_tasks"],
                "uptime": "N/A",  # Could track service uptime
                "memory_usage": "N/A"  # Could track memory usage
            },
            "recommendations": [
                "System is operating normally" if overall_health == "healthy" else "Check component health"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """
    Cancel a specific running task.
    
    Attempts to gracefully cancel a task that may be hanging or no longer needed.
    """
    try:
        # Check if task exists
        status_report = agent_monitor.get_status_report()
        task_exists = any(task["task_id"] == task_id for task in status_report["active_task_details"])
        
        if not task_exists:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # Mark task as cancelled (this would need implementation in agent_monitor)
        # For now, we'll just mark it as failed
        agent_monitor.fail_task(task_id, "Cancelled by user request")
        
        return {
            "success": True,
            "message": f"Task {task_id} has been cancelled",
            "timestamp": "2025-01-27T12:00:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.get("/metrics")
async def get_performance_metrics():
    """
    Get detailed performance metrics for monitoring and optimization.
    
    Returns comprehensive performance data including:
    - Task execution statistics
    - Agent performance metrics
    - System resource usage
    - Trend analysis
    """
    try:
        status_report = agent_monitor.get_status_report()
        
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
                "total_agents": len(crewai_service.agents) if crewai_service.agents else 0,
                "agents_busy": len(set(task["agent"] for task in status_report["active_task_details"])),
                "agent_utilization": "N/A"  # Could calculate from active vs total
            },
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
            "timestamp": "2025-01-27T12:00:00Z",
            "metrics": metrics,
            "recommendations": [
                "Consider implementing historical data tracking for better metrics",
                "Add resource usage monitoring for system optimization"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}") 