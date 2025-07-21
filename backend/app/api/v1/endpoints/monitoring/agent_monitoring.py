"""
Agent monitoring endpoints.

Provides real-time observability into agent status, task execution, and registry management.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from app.services.agent_monitor import agent_monitor, TaskStatus
from app.services.agent_registry import agent_registry, AgentPhase, AgentStatus
from app.core.logging import get_logger as enhanced_get_logger
from .base import get_monitoring_context

logger = enhanced_get_logger(__name__)

router = APIRouter()


@router.get("/status")
async def get_agent_status(
    include_individual_agents: bool = Query(default=False, description="Include individual agent performance data"),
    context = Depends(get_monitoring_context)
):
    """
    Get current agent monitoring status with comprehensive registry data.
    
    Returns real-time information about active agents, running tasks,
    and system health organized by phases for display in the frontend.
    Enhanced with individual agent performance data when requested.
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
        
        response = {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
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
        
        # Add individual agent performance if requested
        if include_individual_agents and context:
            try:
                from app.services.agent_performance_aggregation_service import agent_performance_aggregation_service
                
                # Get performance summary for all agents
                agent_summaries = agent_performance_aggregation_service.get_all_agents_summary(
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    days=7
                )
                
                # Add to response
                response["individual_agent_performance"] = {
                    "period_days": 7,
                    "agents": agent_summaries,
                    "data_source": "agent_performance_daily"
                }
            except Exception as perf_error:
                logger.warning(f"Could not fetch individual agent performance: {perf_error}")
                response["individual_agent_performance"] = {
                    "error": "Performance data temporarily unavailable",
                    "agents": []
                }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {str(e)}")


@router.get("/tasks")
async def get_task_history(
    agent_id: Optional[str] = None, 
    limit: int = Query(default=10, ge=1, le=500),
    include_performance_data: bool = Query(default=False, description="Include detailed performance metrics"),
    context = Depends(get_monitoring_context)
):
    """
    Get task execution history with optional performance data.
    
    Args:
        agent_id: Optional agent ID to filter tasks
        limit: Maximum number of tasks to return
        include_performance_data: Include detailed performance metrics from database
    
    Returns:
        List of recent task executions with details
    """
    try:
        status_report = agent_monitor.get_status_report()
        
        # Filter by agent if specified
        tasks = status_report.get("completed_task_details", [])
        
        if agent_id:
            tasks = [task for task in tasks if task.get("agent") == agent_id]
        
        # Sort by completion time and limit
        tasks = sorted(tasks, key=lambda x: x.get("end_time", ""), reverse=True)[:limit]
        
        response = {
            "success": True,
            "tasks": tasks,
            "total_returned": len(tasks),
            "filtered_by_agent": agent_id is not None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add performance data if requested and context available
        if include_performance_data and context:
            try:
                from app.services.agent_task_history_service import AgentTaskHistoryService
                from app.core.database import get_db
                
                db = next(get_db())
                service = AgentTaskHistoryService(db)
                
                # Get task history from database for more detailed metrics
                if agent_id:
                    db_history = service.get_agent_task_history(
                        agent_name=agent_id,
                        client_account_id=context.client_account_id,
                        engagement_id=context.engagement_id,
                        limit=limit
                    )
                    
                    if "tasks" in db_history:
                        response["detailed_tasks"] = db_history["tasks"]
                        response["performance_metrics"] = {
                            "total_in_database": db_history.get("total_tasks", 0),
                            "data_source": "agent_task_history"
                        }
                
                db.close()
            except Exception as perf_error:
                logger.warning(f"Could not fetch detailed performance data: {perf_error}")
                response["performance_metrics"] = {
                    "error": "Detailed data temporarily unavailable"
                }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting task history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task history: {str(e)}")


@router.get("/agents")
async def get_agent_details():
    """
    Get detailed information about ALL available agents from all sources.
    
    Returns comprehensive agent information including:
    - Agent registry agents (observability phase)
    - Phase 2 crew system agents (discovery, assessment, collection phases)
    - Individual flow agents from various flow systems
    - Current availability status and performance history
    """
    try:
        agent_details_by_phase = {}
        
        # === 1. GET AGENTS FROM AGENT REGISTRY ===
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
                    "source": "agent_registry",
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
            
            # Store agents for this phase
            if agents_list:
                agent_details_by_phase[phase.value] = {
                    "phase_name": phase.value.replace('_', ' ').title(),
                    "total_agents": len(agents_list),
                    "active_agents": len([a for a in agents_list if a["status"]["current_status"] == "active"]),
                    "agents": agents_list
                }
        
        # === 2. GET AGENTS FROM PHASE 2 CREW SYSTEM ===
        try:
            from app.services.crews.factory import CrewFactory
            
            available_crews = CrewFactory.list_crews()
            logger.info(f"Found {len(available_crews)} crew types from Phase 2 system")
            
            for crew_type in available_crews:
                try:
                    crew_info = CrewFactory.get_crew_info(crew_type)
                    if not crew_info:
                        continue
                        
                    # Create crew to get agent composition
                    crew = CrewFactory.create_crew(crew_type)
                    if crew:
                        try:
                            sample_inputs = {"raw_data": [{"sample": "data"}]}
                            crew.initialize_crew(sample_inputs)
                            
                            # Determine phase for crew type
                            if crew_type in ["field_mapping", "data_cleansing", "asset_inventory", "data_import_validation", "attribute_mapping"]:
                                crew_phase = "discovery"
                            elif crew_type in ["sixr_strategy", "complexity_assessment", "risk_analysis"]:  
                                crew_phase = "assessment"
                            elif crew_type in ["gap_analysis", "automated_collection", "collection_orchestrator"]:
                                crew_phase = "collection"
                            else:
                                crew_phase = "discovery"  # Default
                            
                            for i, agent in enumerate(crew.agents):
                                agent_info = {
                                    "agent_id": f"{crew_type}_agent_{i+1}",
                                    "name": f"{crew_info['name']} Agent {i+1}",
                                    "role": getattr(agent, 'role', f"Crew Agent {i+1}"),
                                    "expertise": crew_info.get('description', 'Phase 2 crew-based agent'),
                                    "specialization": getattr(agent, 'backstory', '')[:100] + "..." if len(getattr(agent, 'backstory', '')) > 100 else getattr(agent, 'backstory', ''),
                                    "key_skills": [crew_type.replace('_', ' ').title(), "Crew Collaboration", "Task Execution"],
                                    "capabilities": [f"Tools: {len(getattr(agent, 'tools', []))}", "CrewAI Integration", "Phase 2 System"],
                                    "api_endpoints": [f"/api/v1/crews/{crew_type}/status"],
                                    "description": f"Phase 2 crew-based agent from {crew_info['name']} crew",
                                    "version": "2.0.0",
                                    "source": "phase2_crew_system",
                                    "crew_type": crew_type,
                                    "status": {
                                        "current_status": "active",
                                        "available": True,
                                        "currently_working": False,
                                        "health": "healthy"
                                    },
                                    "features": {
                                        "learning_enabled": True,
                                        "cross_page_communication": False,
                                        "modular_handlers": True
                                    },
                                    "performance": {
                                        "tasks_completed": "N/A",
                                        "success_rate": "N/A", 
                                        "avg_execution_time": "N/A"
                                    },
                                    "registration_time": datetime.utcnow().isoformat(),
                                    "last_heartbeat": datetime.utcnow().isoformat()
                                }
                                
                                # Add to appropriate phase
                                if crew_phase not in agent_details_by_phase:
                                    agent_details_by_phase[crew_phase] = {
                                        "phase_name": crew_phase.replace('_', ' ').title(),
                                        "total_agents": 0,
                                        "active_agents": 0,
                                        "agents": []
                                    }
                                
                                agent_details_by_phase[crew_phase]["agents"].append(agent_info)
                                agent_details_by_phase[crew_phase]["total_agents"] += 1
                                agent_details_by_phase[crew_phase]["active_agents"] += 1
                        
                        except Exception as crew_init_error:
                            logger.warning(f"Could not initialize crew {crew_type} for agent details: {crew_init_error}")
                            # Add fallback agent data for known crew types
                            fallback_agents = []
                            if crew_type == "field_mapping":
                                fallback_agents = [
                                    {"name": "Field Mapping Specialist", "role": "Data Analyst", "description": "Specialized in semantic field mapping and data structure analysis"},
                                    {"name": "Validation Specialist", "role": "Quality Assurance", "description": "Ensures data mapping accuracy and completeness"}
                                ]
                            elif crew_type == "data_cleansing":
                                fallback_agents = [
                                    {"name": "Data Cleansing Specialist", "role": "Data Quality Expert", "description": "Expert in data standardization and quality improvement"},
                                    {"name": "Format Validator", "role": "Format Specialist", "description": "Validates data formats and consistency"}
                                ]
                            elif crew_type == "asset_inventory":
                                fallback_agents = [
                                    {"name": "Asset Classifier", "role": "Classification Expert", "description": "Classifies and categorizes IT assets for migration planning"},
                                    {"name": "Criticality Assessor", "role": "Risk Analyst", "description": "Assesses business criticality and migration priority"}
                                ]
                            
                            crew_phase = "discovery" if crew_type in ["field_mapping", "data_cleansing", "asset_inventory"] else "assessment"
                            
                            for i, fallback in enumerate(fallback_agents):
                                agent_info = {
                                    "agent_id": f"{crew_type}_fallback_{i+1}",
                                    "name": fallback["name"],
                                    "role": fallback["role"],
                                    "expertise": fallback["description"],
                                    "specialization": f"Phase 2 {crew_type.replace('_', ' ')} specialist",
                                    "key_skills": [crew_type.replace('_', ' ').title(), "CrewAI Framework"],
                                    "capabilities": ["Phase 2 System", "Crew-based Processing"],
                                    "api_endpoints": [f"/api/v1/crews/{crew_type}/status"],
                                    "description": f"Phase 2 fallback agent for {crew_type} crew",
                                    "version": "2.0.0",
                                    "source": "phase2_crew_system_fallback",
                                    "crew_type": crew_type,
                                    "status": {
                                        "current_status": "inactive",
                                        "available": False,
                                        "currently_working": False,
                                        "health": "inactive"
                                    },
                                    "features": {
                                        "learning_enabled": True,
                                        "cross_page_communication": False,
                                        "modular_handlers": True
                                    },
                                    "performance": {
                                        "tasks_completed": "N/A",
                                        "success_rate": "N/A",
                                        "avg_execution_time": "N/A"
                                    },
                                    "registration_time": datetime.utcnow().isoformat(),
                                    "last_heartbeat": None
                                }
                                
                                if crew_phase not in agent_details_by_phase:
                                    agent_details_by_phase[crew_phase] = {
                                        "phase_name": crew_phase.replace('_', ' ').title(),
                                        "total_agents": 0,
                                        "active_agents": 0,
                                        "agents": []
                                    }
                                
                                agent_details_by_phase[crew_phase]["agents"].append(agent_info)
                                agent_details_by_phase[crew_phase]["total_agents"] += 1
                except Exception as e:
                    logger.warning(f"Error processing crew {crew_type}: {e}")
                    
        except Exception as e:
            logger.warning(f"Phase 2 crew system not available: {e}")
        
        # === 3. ADD INDIVIDUAL FLOW AGENTS ===
        # These are the specialized agents mentioned in the Discovery Flow Redesign
        individual_agents = [
            {
                "agent_id": "data_import_validation_individual",
                "name": "Data Import Validation Agent",
                "role": "Data Import Specialist", 
                "phase": "discovery",
                "expertise": "Individual specialized agent for data import validation",
                "specialization": "Part of Discovery Flow Redesign - replaces old registry system",
                "key_skills": ["Data Validation", "Import Processing", "Quality Checks"],
                "capabilities": ["Individual Processing", "Discovery Flow Integration", "Real-time Validation"],
                "api_endpoints": ["/api/v1/discovery/data-import/validate"],
                "description": "Individual specialized agent from Discovery Flow Redesign",
                "status": "active",
                "source": "individual_flow_agents"
            },
            {
                "agent_id": "attribute_mapping_individual", 
                "name": "Attribute Mapping Agent",
                "role": "Attribute Mapping Specialist",
                "phase": "discovery", 
                "expertise": "Individual specialized agent for attribute mapping",
                "specialization": "Part of Discovery Flow Redesign - field mapping intelligence",
                "key_skills": ["Attribute Mapping", "Field Analysis", "Semantic Matching"],
                "capabilities": ["Individual Processing", "Discovery Flow Integration", "Learning Enabled"],
                "api_endpoints": ["/api/v1/discovery/attribute-mapping"],
                "description": "Individual specialized agent from Discovery Flow Redesign",
                "status": "active",
                "source": "individual_flow_agents"
            },
            {
                "agent_id": "data_cleansing_individual",
                "name": "Data Cleansing Agent", 
                "role": "Data Cleansing Specialist",
                "phase": "discovery",
                "expertise": "Individual specialized agent for data cleansing",
                "specialization": "Part of Discovery Flow Redesign - data quality improvement", 
                "key_skills": ["Data Cleansing", "Quality Assessment", "Data Standardization"],
                "capabilities": ["Individual Processing", "Discovery Flow Integration", "Quality Intelligence"],
                "api_endpoints": ["/api/v1/discovery/data-cleansing"],
                "description": "Individual specialized agent from Discovery Flow Redesign", 
                "status": "active",
                "source": "individual_flow_agents"
            }
        ]
        
        for individual_agent in individual_agents:
            phase = individual_agent["phase"]
            
            agent_info = {
                "agent_id": individual_agent["agent_id"],
                "name": individual_agent["name"],
                "role": individual_agent["role"],
                "expertise": individual_agent["expertise"],
                "specialization": individual_agent["specialization"],
                "key_skills": individual_agent["key_skills"],
                "capabilities": individual_agent["capabilities"],
                "api_endpoints": individual_agent["api_endpoints"],
                "description": individual_agent["description"],
                "version": "3.0.0",  # Discovery Flow Redesign version
                "source": individual_agent["source"],
                "status": {
                    "current_status": individual_agent["status"],
                    "available": individual_agent["status"] == "active",
                    "currently_working": False,
                    "health": "healthy" if individual_agent["status"] == "active" else "inactive"
                },
                "features": {
                    "learning_enabled": True,
                    "cross_page_communication": True,
                    "modular_handlers": True
                },
                "performance": {
                    "tasks_completed": "N/A",
                    "success_rate": "N/A",
                    "avg_execution_time": "N/A"
                },
                "registration_time": datetime.utcnow().isoformat(),
                "last_heartbeat": datetime.utcnow().isoformat()
            }
            
            if phase not in agent_details_by_phase:
                agent_details_by_phase[phase] = {
                    "phase_name": phase.replace('_', ' ').title(),
                    "total_agents": 0,
                    "active_agents": 0,
                    "agents": []
                }
            
            agent_details_by_phase[phase]["agents"].append(agent_info)
            agent_details_by_phase[phase]["total_agents"] += 1
            if individual_agent["status"] == "active":
                agent_details_by_phase[phase]["active_agents"] += 1
        
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