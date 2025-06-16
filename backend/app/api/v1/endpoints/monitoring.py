"""
Agent Monitoring API Endpoints
Provides real-time observability into CrewAI agent task execution for the frontend.
Enhanced with comprehensive agent registry and phase organization.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from app.services.agent_monitor import agent_monitor, TaskStatus

# Import the new agent registry
from app.services.agent_registry import agent_registry, AgentPhase, AgentStatus

# Import CrewAI Flow service and context dependencies
from app.api.v1.dependencies import get_crewai_flow_service
from app.core.context import RequestContext, extract_context_from_request
from app.services.crewai_flow_service import CrewAIFlowService

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


@router.get("/crewai-flows")
async def get_crewai_flow_status(
    request: Request,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """
    Get comprehensive CrewAI Flow monitoring data.
    
    Returns detailed information about:
    - Active discovery flows and their current phases
    - Flow execution progress and status
    - Agent task details within flows
    - Flow performance metrics
    - Error states and debugging information
    """
    try:
        # Get context without authentication
        context = extract_context_from_request(request)
        
        # Get active flows summary
        flows_summary = service.get_active_flows_summary()
        
        # Get all active flows with details
        active_flows = service.get_all_active_flows(context)
        
        # Get service health status
        health_status = service.get_health_status()
        
        # Get performance metrics
        performance_metrics = service.get_performance_metrics()
        
        # Enhanced flow details with agent task information
        enhanced_flows = []
        for flow in active_flows:
            flow_id = flow.get("session_id")
            if flow_id:
                # Get detailed flow status
                flow_status = service.get_flow_status(flow_id)
                
                # Combine flow data with status details
                enhanced_flow = {
                    **flow,
                    "detailed_status": flow_status,
                    "agent_tasks": flow_status.get("agent_tasks", []),
                    "current_agent": flow_status.get("current_agent"),
                    "execution_timeline": flow_status.get("execution_timeline", []),
                    "performance_metrics": flow_status.get("performance_metrics", {}),
                    "error_details": flow_status.get("errors", [])
                }
                enhanced_flows.append(enhanced_flow)
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "crewai_flows": {
                "service_health": health_status,
                "flows_summary": flows_summary,
                "active_flows": enhanced_flows,
                "performance_metrics": performance_metrics,
                "total_active_flows": len(enhanced_flows),
                "openlit_available": getattr(service, 'OPENLIT_AVAILABLE', False)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting CrewAI flow status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get CrewAI flow status: {str(e)}")


@router.get("/crewai-flows/{session_id}")
async def get_specific_flow_details(
    session_id: str,
    request: Request,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """
    Get detailed information about a specific CrewAI Flow.
    
    Returns comprehensive flow execution details including:
    - Current flow state and phase
    - Agent task execution history
    - Flow execution timeline
    - Performance metrics for this specific flow
    - Error states and debugging information
    - Real-time agent activity
    """
    try:
        # Get context without authentication
        context = extract_context_from_request(request)
        
        # Get flow state
        flow_state = await service.get_flow_state_by_session(session_id, context)
        if not flow_state:
            raise HTTPException(status_code=404, detail=f"Flow not found: {session_id}")
        
        # Get detailed flow status
        flow_status = service.get_flow_status(session_id)
        
        # Combine all flow information
        detailed_flow = {
            "session_id": session_id,
            "flow_state": flow_state,
            "flow_status": flow_status,
            "agent_tasks": flow_status.get("agent_tasks", []),
            "current_agent": flow_status.get("current_agent"),
            "execution_timeline": flow_status.get("execution_timeline", []),
            "performance_metrics": flow_status.get("performance_metrics", {}),
            "error_details": flow_status.get("errors", []),
            "debug_info": {
                "phases_completed": flow_state.get("phases_completed", {}),
                "current_phase": flow_state.get("current_phase"),
                "status": flow_state.get("status"),
                "progress_percentage": flow_state.get("progress_percentage", 0),
                "warnings": flow_state.get("warnings", []),
                "metadata": flow_state.get("metadata", {})
            }
        }
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "flow_details": detailed_flow
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flow details for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get flow details: {str(e)}")


@router.get("/crewai-flows/{session_id}/agent-tasks")
async def get_flow_agent_tasks(
    session_id: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """
    Get detailed agent task information for a specific flow.
    
    Returns real-time agent task execution details including:
    - Current agent tasks and their status
    - Task execution timeline
    - Agent performance within this flow
    - Task dependencies and execution order
    - Error states and retry information
    """
    try:
        # Get flow status with focus on agent tasks
        flow_status = service.get_flow_status(session_id)
        
        if not flow_status:
            raise HTTPException(status_code=404, detail=f"Flow not found: {session_id}")
        
        # Extract and enhance agent task information
        agent_tasks = flow_status.get("agent_tasks", [])
        current_agent = flow_status.get("current_agent")
        execution_timeline = flow_status.get("execution_timeline", [])
        
        # Organize tasks by agent and phase
        tasks_by_agent = {}
        tasks_by_phase = {}
        
        for task in agent_tasks:
            agent_name = task.get("agent_name", "unknown")
            phase = task.get("phase", "unknown")
            
            if agent_name not in tasks_by_agent:
                tasks_by_agent[agent_name] = []
            tasks_by_agent[agent_name].append(task)
            
            if phase not in tasks_by_phase:
                tasks_by_phase[phase] = []
            tasks_by_phase[phase].append(task)
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "agent_tasks": {
                "current_agent": current_agent,
                "all_tasks": agent_tasks,
                "tasks_by_agent": tasks_by_agent,
                "tasks_by_phase": tasks_by_phase,
                "execution_timeline": execution_timeline,
                "total_tasks": len(agent_tasks),
                "completed_tasks": len([t for t in agent_tasks if t.get("status") == "completed"]),
                "active_tasks": len([t for t in agent_tasks if t.get("status") == "running"]),
                "failed_tasks": len([t for t in agent_tasks if t.get("status") == "failed"])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent tasks for flow {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent tasks: {str(e)}")


# Create a simple context dependency for monitoring (no auth required)
async def get_monitoring_context(request: Request) -> RequestContext:
    """Get context for monitoring endpoints without authentication."""
    return extract_context_from_request(request)