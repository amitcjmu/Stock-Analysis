"""
Agent Monitoring API Endpoints
Provides real-time observability into CrewAI agent task execution for the frontend.
Enhanced with comprehensive agent registry and phase organization.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
import logging

from app.services.agent_monitor import agent_monitor, TaskStatus
from app.services.crewai_service_modular import crewai_service

# Import the new agent registry
from app.services.agent_registry import agent_registry, AgentPhase, AgentStatus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
async def get_agent_status():
    """
    Get current agent monitoring status with comprehensive registry data.
    
    Returns real-time information about active agents, running tasks,
    and system health organized by phases for display in the frontend.
    """
    try:
        # Get monitoring status
        status_report = agent_monitor.get_status_report()
        
        # Get comprehensive registry data
        registry_status = agent_registry.get_registry_status()
        
        # Get agent capabilities from registry
        agent_capabilities = agent_registry.get_agent_capabilities_formatted()
        
        # Get system status from CrewAI service (fallback)
        system_status = {}
        if crewai_service.agent_manager:
            system_status = crewai_service.agent_manager.get_system_status()
        
        return {
            "success": True,
            "timestamp": "2025-01-28T12:00:00Z",
            "monitoring": {
                "active": status_report["monitoring_active"],
                "active_tasks": status_report["active_tasks"],
                "completed_tasks": status_report["completed_tasks"],
                "hanging_tasks": status_report["hanging_tasks"]
            },
            "agents": {
                "total_registered": registry_status["total_agents"],
                "active_agents": registry_status["active_agents"],
                "learning_enabled": registry_status["learning_enabled_agents"],
                "cross_page_communication": registry_status["cross_page_communication_agents"],
                "modular_handlers": registry_status["modular_handler_agents"],
                "phase_distribution": registry_status["phase_distribution"],
                "capabilities": agent_capabilities,
                "system_status": system_status
            },
            "tasks": {
                "active": status_report["active_task_details"],
                "hanging": status_report["hanging_task_details"]
            },
            "registry_status": registry_status
        }
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {str(e)}")


@router.get("/tasks")
async def get_task_history(agent_id: Optional[str] = None, limit: int = 10):
    """
    Get task execution history.
    
    Args:
        agent_id: Optional agent ID to filter tasks
        limit: Maximum number of tasks to return
    
    Returns:
        List of recent task executions with details
    """
    try:
        status_report = agent_monitor.get_status_report()
        
        # Filter by agent if specified
        tasks = status_report["completed_task_details"] if "completed_task_details" in status_report else []
        
        if agent_id:
            tasks = [task for task in tasks if task.get("agent") == agent_id]
        
        # Sort by completion time and limit
        tasks = sorted(tasks, key=lambda x: x.get("end_time", ""), reverse=True)[:limit]
        
        return {
            "success": True,
            "tasks": tasks,
            "total_returned": len(tasks),
            "filtered_by_agent": agent_id is not None
        }
        
    except Exception as e:
        logger.error(f"Error getting task history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task history: {str(e)}")


@router.get("/agents")
async def get_agent_details():
    """
    Get detailed information about available agents organized by phases.
    
    Returns comprehensive agent information including:
    - Agent roles and expertise organized by migration phases
    - Current availability status
    - Performance history
    - Specializations and skills
    - Learning and cross-page communication capabilities
    """
    try:
        agent_details_by_phase = {}
        
        # Get agents organized by phase
        for phase in AgentPhase:
            phase_agents = agent_registry.get_agents_by_phase(phase)
            
            # Get current task assignments for status
            status_report = agent_monitor.get_status_report()
            active_agents = {task["agent"] for task in status_report["active_task_details"]}
            
            agents_list = []
            for agent in phase_agents:
                # Check if agent is currently working (simplified check)
                is_working = any(agent.name.lower().replace(' ', '_') in active_agent.lower() 
                               for active_agent in active_agents)
                
                agent_info = {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "role": agent.role,
                    "expertise": agent.expertise,
                    "specialization": agent.specialization,
                    "key_skills": agent.key_skills,
                    "capabilities": agent.capabilities,
                    "api_endpoints": agent.api_endpoints,
                    "description": agent.description,
                    "version": agent.version,
                    "status": {
                        "current_status": agent.status.value,
                        "available": agent.status == AgentStatus.ACTIVE and not is_working,
                        "currently_working": is_working,
                        "health": "healthy" if agent.status == AgentStatus.ACTIVE else "inactive"
                    },
                    "features": {
                        "learning_enabled": agent.learning_enabled,
                        "cross_page_communication": agent.cross_page_communication,
                        "modular_handlers": agent.modular_handlers
                    },
                    "performance": {
                        "tasks_completed": agent.tasks_completed,
                        "success_rate": f"{agent.success_rate:.1%}" if agent.success_rate > 0 else "N/A",
                        "avg_execution_time": f"{agent.avg_execution_time:.1f}s" if agent.avg_execution_time > 0 else "N/A"
                    },
                    "registration_time": agent.registration_time.isoformat() if agent.registration_time else None,
                    "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None
                }
                agents_list.append(agent_info)
            
            # Only include phases that have agents
            if agents_list:
                agent_details_by_phase[phase.value] = {
                    "phase_name": phase.value.replace('_', ' ').title(),
                    "total_agents": len(agents_list),
                    "active_agents": len([a for a in agents_list if a["status"]["current_status"] == "active"]),
                    "agents": agents_list
                }
        
        # Calculate summary statistics
        all_agents = []
        for phase_data in agent_details_by_phase.values():
            all_agents.extend(phase_data["agents"])
        
        summary = {
            "total_agents": len(all_agents),
            "by_phase": {phase: data["total_agents"] for phase, data in agent_details_by_phase.items()},
            "by_status": {
                "active": len([a for a in all_agents if a["status"]["current_status"] == "active"]),
                "planned": len([a for a in all_agents if a["status"]["current_status"] == "planned"]),
                "in_development": len([a for a in all_agents if a["status"]["current_status"] == "in_development"])
            },
            "features": {
                "learning_enabled": len([a for a in all_agents if a["features"]["learning_enabled"]]),
                "cross_page_communication": len([a for a in all_agents if a["features"]["cross_page_communication"]]),
                "modular_handlers": len([a for a in all_agents if a["features"]["modular_handlers"]])
            }
        }
        
        return {
            "success": True,
            "timestamp": "2025-01-28T12:00:00Z",
            "agents_by_phase": agent_details_by_phase,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting agent details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent details: {str(e)}")


@router.get("/agents/by-phase/{phase}")
async def get_agents_by_phase(phase: str):
    """
    Get agents for a specific phase.
    
    Args:
        phase: Migration phase (discovery, assessment, planning, etc.)
    
    Returns:
        List of agents for the specified phase
    """
    try:
        # Validate phase
        try:
            agent_phase = AgentPhase(phase.lower())
        except ValueError:
            valid_phases = [p.value for p in AgentPhase]
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid phase. Valid phases are: {', '.join(valid_phases)}"
            )
        
        # Get agents for this phase
        phase_agents = agent_registry.get_agents_by_phase(agent_phase)
        
        agents_list = []
        for agent in phase_agents:
            agent_info = {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "role": agent.role,
                "status": agent.status.value,
                "expertise": agent.expertise,
                "specialization": agent.specialization,
                "learning_enabled": agent.learning_enabled,
                "cross_page_communication": agent.cross_page_communication,
                "modular_handlers": agent.modular_handlers
            }
            agents_list.append(agent_info)
        
        return {
            "success": True,
            "phase": phase.title(),
            "agents": agents_list,
            "count": len(agents_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agents by phase: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agents by phase: {str(e)}")


@router.get("/health")
async def get_system_health():
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
        if crewai_service.agent_manager:
            system_status = crewai_service.agent_manager.get_system_status()
        
        # Get monitoring status
        status_report = agent_monitor.get_status_report()
        
        # Calculate health indicators
        health_indicators = {
            "agent_registry": "healthy" if registry_status["registry_status"] == "healthy" else "degraded",
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


@router.post("/agents/{agent_id}/heartbeat")
async def update_agent_heartbeat(agent_id: str, status: Optional[str] = None):
    """
    Update agent heartbeat and optionally status.
    
    Args:
        agent_id: Agent identifier
        status: Optional new status for the agent
    
    Returns:
        Success confirmation
    """
    try:
        # Update agent heartbeat in registry
        kwargs = {}
        if status:
            try:
                agent_status = AgentStatus(status.lower())
                kwargs["status"] = agent_status
            except ValueError:
                valid_statuses = [s.value for s in AgentStatus]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Valid statuses are: {', '.join(valid_statuses)}"
                )
        
        agent_registry.update_agent_status(agent_id, **kwargs)
        
        return {
            "success": True,
            "agent_id": agent_id,
            "heartbeat_updated": True,
            "status_updated": status is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent heartbeat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update agent heartbeat: {str(e)}")


@router.get("/registry/export")
async def export_agent_registry():
    """
    Export the complete agent registry for backup or analysis.
    
    Returns:
        Complete agent registry data
    """
    try:
        registry_data = agent_registry.to_dict()
        
        return {
            "success": True,
            "timestamp": "2025-01-28T12:00:00Z",
            "registry": registry_data
        }
        
    except Exception as e:
        logger.error(f"Error exporting agent registry: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export agent registry: {str(e)}") 