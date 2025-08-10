"""
Agent monitoring endpoints.

Provides real-time observability into agent status, task execution, and registry management.
"""

from datetime import datetime
from typing import Dict, Optional, Any, List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.logging import get_logger as enhanced_get_logger
from app.services.agent_monitor import agent_monitor
from app.services.agent_registry import AgentPhase, AgentStatus, agent_registry

from .base import get_monitoring_context

logger = enhanced_get_logger(__name__)

router = APIRouter()


def _safe_get_dict_value(
    data: Dict[str, Any], key: str, default: Any = None, expected_type: type = None
) -> Any:
    """Safely get a value from a dictionary with type checking.

    Args:
        data: Dictionary to access
        key: Key to retrieve
        default: Default value if key doesn't exist
        expected_type: Expected type for validation

    Returns:
        Value from dictionary or default if not found/invalid type
    """
    if not isinstance(data, dict):
        logger.warning(f"Expected dict for safe access, got {type(data)}")
        return default

    value = data.get(key, default)

    if expected_type and value is not None and not isinstance(value, expected_type):
        logger.warning(
            f"Expected {expected_type} for key '{key}', got {type(value)}. Using default."
        )
        return default

    return value


def _safe_get_nested_dict_value(
    data: Dict[str, Any], keys: List[str], default: Any = None
) -> Any:
    """Safely get a nested value from a dictionary.

    Args:
        data: Dictionary to access
        keys: List of keys for nested access
        default: Default value if any key doesn't exist

    Returns:
        Value from nested dictionary or default if not found
    """
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def _validate_status_report(status_report: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize status report data.

    Args:
        status_report: Raw status report from agent monitor

    Returns:
        Sanitized status report with safe defaults
    """
    if not isinstance(status_report, dict):
        logger.error("Status report is not a dictionary, using defaults")
        return {
            "monitoring_active": False,
            "active_tasks": 0,
            "completed_tasks": 0,
            "hanging_tasks": 0,
            "active_task_details": [],
            "hanging_task_details": [],
            "completed_task_details": [],
        }

    return {
        "monitoring_active": _safe_get_dict_value(
            status_report, "monitoring_active", False, bool
        ),
        "active_tasks": _safe_get_dict_value(status_report, "active_tasks", 0, int),
        "completed_tasks": _safe_get_dict_value(
            status_report, "completed_tasks", 0, int
        ),
        "hanging_tasks": _safe_get_dict_value(status_report, "hanging_tasks", 0, int),
        "active_task_details": _safe_get_dict_value(
            status_report, "active_task_details", [], list
        ),
        "hanging_task_details": _safe_get_dict_value(
            status_report, "hanging_task_details", [], list
        ),
        "completed_task_details": _safe_get_dict_value(
            status_report, "completed_task_details", [], list
        ),
    }


def _validate_registry_status(registry_status: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize registry status data.

    Args:
        registry_status: Raw registry status data

    Returns:
        Sanitized registry status with safe defaults
    """
    if not isinstance(registry_status, dict):
        logger.error("Registry status is not a dictionary, using defaults")
        return {
            "total_agents": 0,
            "active_agents": 0,
            "learning_enabled_agents": 0,
            "cross_page_communication_agents": 0,
            "modular_handler_agents": 0,
            "phase_distribution": {},
        }

    return {
        "total_agents": _safe_get_dict_value(registry_status, "total_agents", 0, int),
        "active_agents": _safe_get_dict_value(registry_status, "active_agents", 0, int),
        "learning_enabled_agents": _safe_get_dict_value(
            registry_status, "learning_enabled_agents", 0, int
        ),
        "cross_page_communication_agents": _safe_get_dict_value(
            registry_status, "cross_page_communication_agents", 0, int
        ),
        "modular_handler_agents": _safe_get_dict_value(
            registry_status, "modular_handler_agents", 0, int
        ),
        "phase_distribution": _safe_get_dict_value(
            registry_status, "phase_distribution", {}, dict
        ),
    }


@router.get("/status")
async def get_agent_status(
    include_individual_agents: bool = Query(
        default=False, description="Include individual agent performance data"
    ),
    context=Depends(get_monitoring_context),
):
    """
    Get current agent monitoring status with comprehensive registry data.

    Returns real-time information about active agents, running tasks,
    and system health organized by phases for display in the frontend.
    Enhanced with individual agent performance data when requested.
    """
    try:
        # Get monitoring status with validation
        raw_status_report = agent_monitor.get_status_report()
        status_report = _validate_status_report(raw_status_report)

        # Get comprehensive registry data with validation
        raw_registry_status = agent_registry.get_registry_status()
        registry_status = _validate_registry_status(raw_registry_status)

        # Get agent capabilities from registry with error handling
        try:
            agent_capabilities = agent_registry.get_agent_capabilities_formatted()
            if not isinstance(agent_capabilities, (list, dict)):
                agent_capabilities = []
        except Exception as cap_error:
            logger.warning(f"Could not fetch agent capabilities: {cap_error}")
            agent_capabilities = []

        # Get system status from CrewAI service (fallback)
        system_status = {}

        response = {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "monitoring": {
                "active": status_report["monitoring_active"],
                "active_tasks": status_report["active_tasks"],
                "completed_tasks": status_report["completed_tasks"],
                "hanging_tasks": status_report["hanging_tasks"],
            },
            "agents": {
                "total_registered": registry_status["total_agents"],
                "active_agents": registry_status["active_agents"],
                "learning_enabled": registry_status["learning_enabled_agents"],
                "cross_page_communication": registry_status[
                    "cross_page_communication_agents"
                ],
                "modular_handlers": registry_status["modular_handler_agents"],
                "phase_distribution": registry_status["phase_distribution"],
                "capabilities": agent_capabilities,
                "system_status": system_status,
            },
            "tasks": {
                "active": status_report["active_task_details"],
                "hanging": status_report["hanging_task_details"],
            },
            "registry_status": registry_status,
        }

        # Add individual agent performance if requested
        if include_individual_agents and context:
            try:
                from app.services.agent_performance_aggregation_service import (
                    agent_performance_aggregation_service,
                )

                # Get performance summary for all agents
                agent_summaries = (
                    agent_performance_aggregation_service.get_all_agents_summary(
                        client_account_id=context.client_account_id,
                        engagement_id=context.engagement_id,
                        days=7,
                    )
                )

                # Add to response
                response["individual_agent_performance"] = {
                    "period_days": 7,
                    "agents": agent_summaries,
                    "data_source": "agent_performance_daily",
                }
            except Exception as perf_error:
                logger.warning(
                    f"Could not fetch individual agent performance: {perf_error}"
                )
                response["individual_agent_performance"] = {
                    "error": "Performance data temporarily unavailable",
                    "agents": [],
                }

        return response

    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent status: {str(e)}"
        )


@router.get("/tasks")
async def get_task_history(
    agent_id: Optional[str] = None,
    limit: int = Query(default=10, ge=1, le=500),
    include_performance_data: bool = Query(
        default=False, description="Include detailed performance metrics"
    ),
    context=Depends(get_monitoring_context),
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
        raw_status_report = agent_monitor.get_status_report()
        status_report = _validate_status_report(raw_status_report)

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
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Add performance data if requested and context available
        if include_performance_data and context:
            try:
                from app.core.database import get_db
                from app.services.agent_task_history_service import (
                    AgentTaskHistoryService,
                )

                db = next(get_db())
                service = AgentTaskHistoryService(db)

                # Get task history from database for more detailed metrics
                if agent_id:
                    db_history = service.get_agent_task_history(
                        agent_name=agent_id,
                        client_account_id=context.client_account_id,
                        engagement_id=context.engagement_id,
                        limit=limit,
                    )

                    if "tasks" in db_history:
                        response["detailed_tasks"] = db_history["tasks"]
                        response["performance_metrics"] = {
                            "total_in_database": db_history.get("total_tasks", 0),
                            "data_source": "agent_task_history",
                        }

                db.close()
            except Exception as perf_error:
                logger.warning(
                    f"Could not fetch detailed performance data: {perf_error}"
                )
                response["performance_metrics"] = {
                    "error": "Detailed data temporarily unavailable"
                }

        return response

    except Exception as e:
        logger.error(f"Error getting task history: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get task history: {str(e)}"
        )


def _build_agent_info_from_registry(agent, is_working: bool) -> dict:
    """Build agent info dictionary from registry agent."""
    return {
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
            "health": ("healthy" if agent.status == AgentStatus.ACTIVE else "inactive"),
        },
        "features": {
            "learning_enabled": agent.learning_enabled,
            "cross_page_communication": agent.cross_page_communication,
            "modular_handlers": agent.modular_handlers,
        },
        "performance": {
            "tasks_completed": agent.tasks_completed,
            "success_rate": (
                f"{agent.success_rate:.1%}" if agent.success_rate > 0 else "N/A"
            ),
            "avg_execution_time": (
                f"{agent.avg_execution_time:.1f}s"
                if agent.avg_execution_time > 0
                else "N/A"
            ),
        },
        "registration_time": (
            agent.registration_time.isoformat() if agent.registration_time else None
        ),
        "last_heartbeat": (
            agent.last_heartbeat.isoformat() if agent.last_heartbeat else None
        ),
    }


def _get_agents_from_registry(agent_details_by_phase: dict, status_report: dict):
    """Get agents from agent registry and add to agent_details_by_phase."""
    # Safely get active agents from task details
    active_task_details = _safe_get_dict_value(
        status_report, "active_task_details", [], list
    )
    active_agents = set()
    for task in active_task_details:
        if isinstance(task, dict) and "agent" in task:
            active_agents.add(task["agent"])

    for phase in AgentPhase:
        phase_agents = agent_registry.get_agents_by_phase(phase)
        agents_list = []

        for agent in phase_agents:
            # Check if agent is currently working (simplified check)
            is_working = any(
                agent.name.lower().replace(" ", "_") in active_agent.lower()
                for active_agent in active_agents
            )

            agent_info = _build_agent_info_from_registry(agent, is_working)
            agents_list.append(agent_info)

        # Store agents for this phase
        if agents_list:
            agent_details_by_phase[phase.value] = {
                "phase_name": phase.value.replace("_", " ").title(),
                "total_agents": len(agents_list),
                "active_agents": len(
                    [
                        a
                        for a in agents_list
                        if a["status"]["current_status"] == "active"
                    ]
                ),
                "agents": agents_list,
            }


def _determine_crew_phase(crew_type: str) -> str:
    """Determine the phase for a crew type."""
    if crew_type in [
        "field_mapping",
        "data_cleansing",
        "asset_inventory",
        "data_import_validation",
        "attribute_mapping",
    ]:
        return "discovery"
    elif crew_type in [
        "sixr_strategy",
        "complexity_assessment",
        "risk_analysis",
    ]:
        return "assessment"
    elif crew_type in [
        "gap_analysis",
        "automated_collection",
        "collection_orchestrator",
    ]:
        return "collection"
    else:
        return "discovery"  # Default


def _create_crew_agent_info(crew_type: str, crew_info: dict, agent, i: int) -> dict:
    """Create agent info for a crew agent."""
    crew_phase = _determine_crew_phase(crew_type)

    # Safely get crew info values with defaults
    crew_name = _safe_get_dict_value(
        crew_info, "name", f"Unknown Crew {crew_type}", str
    )
    crew_description = _safe_get_dict_value(
        crew_info, "description", "Phase 2 crew-based agent", str
    )

    # Safely get agent attributes
    agent_role = getattr(agent, "role", f"Crew Agent {i+1}")
    agent_backstory = getattr(agent, "backstory", "")
    agent_tools = getattr(agent, "tools", [])

    # Safely format backstory with length check
    specialization = ""
    if isinstance(agent_backstory, str) and agent_backstory:
        specialization = (
            agent_backstory[:100] + "..."
            if len(agent_backstory) > 100
            else agent_backstory
        )

    return {
        "agent_id": f"{crew_type}_agent_{i+1}",
        "name": f"{crew_name} Agent {i+1}",
        "role": agent_role,
        "expertise": crew_description,
        "specialization": specialization,
        "key_skills": [
            crew_type.replace("_", " ").title(),
            "Crew Collaboration",
            "Task Execution",
        ],
        "capabilities": [
            f"Tools: {len(agent_tools) if isinstance(agent_tools, list) else 0}",
            "CrewAI Integration",
            "Phase 2 System",
        ],
        "api_endpoints": [
            f"/api/v1/crews/{crew_type}/status"
        ],  # NOTE: May need router verification
        "description": f"Phase 2 crew-based agent from {crew_name} crew",
        "version": "2.0.0",
        "source": "phase2_crew_system",
        "crew_type": crew_type,
        "status": {
            "current_status": "active",
            "available": True,
            "currently_working": False,
            "health": "healthy",
        },
        "features": {
            "learning_enabled": True,
            "cross_page_communication": False,
            "modular_handlers": True,
        },
        "performance": {
            "tasks_completed": "N/A",
            "success_rate": "N/A",
            "avg_execution_time": "N/A",
        },
        "registration_time": datetime.utcnow().isoformat(),
        "last_heartbeat": datetime.utcnow().isoformat(),
    }, crew_phase


def _get_fallback_agents_for_crew(crew_type: str) -> list:
    """Get fallback agents for a specific crew type."""
    if crew_type == "field_mapping":
        return [
            {
                "name": "Field Mapping Specialist",
                "role": "Data Analyst",
                "description": (
                    "Specialized in semantic field mapping "
                    "and data structure analysis"
                ),
            },
            {
                "name": "Validation Specialist",
                "role": "Quality Assurance",
                "description": "Ensures data mapping accuracy and completeness",
            },
        ]
    elif crew_type == "data_cleansing":
        return [
            {
                "name": "Data Cleansing Specialist",
                "role": "Data Quality Expert",
                "description": "Expert in data standardization and quality improvement",
            },
            {
                "name": "Format Validator",
                "role": "Format Specialist",
                "description": "Validates data formats and consistency",
            },
        ]
    elif crew_type == "asset_inventory":
        return [
            {
                "name": "Asset Classifier",
                "role": "Classification Expert",
                "description": "Classifies and categorizes IT assets for migration planning",
            },
            {
                "name": "Criticality Assessor",
                "role": "Risk Analyst",
                "description": "Assesses business criticality and migration priority",
            },
        ]
    return []


def _add_fallback_agents(agent_details_by_phase: dict, crew_type: str):
    """Add fallback agents for a crew type."""
    fallback_agents = _get_fallback_agents_for_crew(crew_type)
    crew_phase = _determine_crew_phase(crew_type)

    for i, fallback in enumerate(fallback_agents):
        agent_info = {
            "agent_id": f"{crew_type}_fallback_{i+1}",
            "name": fallback["name"],
            "role": fallback["role"],
            "expertise": fallback["description"],
            "specialization": f"Phase 2 {crew_type.replace('_', ' ')} specialist",
            "key_skills": [
                crew_type.replace("_", " ").title(),
                "CrewAI Framework",
            ],
            "capabilities": [
                "Phase 2 System",
                "Crew-based Processing",
            ],
            "api_endpoints": [
                f"/api/v1/crews/{crew_type}/status"
            ],  # NOTE: May need router verification
            "description": f"Phase 2 fallback agent for {crew_type} crew",
            "version": "2.0.0",
            "source": "phase2_crew_system_fallback",
            "crew_type": crew_type,
            "status": {
                "current_status": "inactive",
                "available": False,
                "currently_working": False,
                "health": "inactive",
            },
            "features": {
                "learning_enabled": True,
                "cross_page_communication": False,
                "modular_handlers": True,
            },
            "performance": {
                "tasks_completed": "N/A",
                "success_rate": "N/A",
                "avg_execution_time": "N/A",
            },
            "registration_time": datetime.utcnow().isoformat(),
            "last_heartbeat": None,
        }

        if crew_phase not in agent_details_by_phase:
            agent_details_by_phase[crew_phase] = {
                "phase_name": crew_phase.replace("_", " ").title(),
                "total_agents": 0,
                "active_agents": 0,
                "agents": [],
            }

        agent_details_by_phase[crew_phase]["agents"].append(agent_info)
        agent_details_by_phase[crew_phase]["total_agents"] += 1


def _add_individual_flow_agents(agent_details_by_phase: dict):
    """Add individual flow agents to agent_details_by_phase."""
    individual_agents = [
        {
            "agent_id": "data_import_validation_individual",
            "name": "Data Import Validation Agent",
            "role": "Data Import Specialist",
            "phase": "discovery",
            "expertise": "Individual specialized agent for data import validation",
            "specialization": "Part of Discovery Flow Redesign - replaces old registry system",
            "key_skills": [
                "Data Validation",
                "Import Processing",
                "Quality Checks",
            ],
            "capabilities": [
                "Individual Processing",
                "Discovery Flow Integration",
                "Real-time Validation",
            ],
            "api_endpoints": [
                "/api/v1/flows/data-import/validate"
            ],  # NOTE: May need router verification
            "description": "Individual specialized agent from Discovery Flow Redesign",
            "status": "active",
            "source": "individual_flow_agents",
        },
        {
            "agent_id": "attribute_mapping_individual",
            "name": "Attribute Mapping Agent",
            "role": "Attribute Mapping Specialist",
            "phase": "discovery",
            "expertise": "Individual specialized agent for attribute mapping",
            "specialization": "Part of Discovery Flow Redesign - field mapping intelligence",
            "key_skills": [
                "Attribute Mapping",
                "Field Analysis",
                "Semantic Matching",
            ],
            "capabilities": [
                "Individual Processing",
                "Discovery Flow Integration",
                "Learning Enabled",
            ],
            "api_endpoints": [
                "/api/v1/flows/attribute-mapping"
            ],  # NOTE: May need router verification
            "description": "Individual specialized agent from Discovery Flow Redesign",
            "status": "active",
            "source": "individual_flow_agents",
        },
        {
            "agent_id": "data_cleansing_individual",
            "name": "Data Cleansing Agent",
            "role": "Data Cleansing Specialist",
            "phase": "discovery",
            "expertise": "Individual specialized agent for data cleansing",
            "specialization": "Part of Discovery Flow Redesign - data quality improvement",
            "key_skills": [
                "Data Cleansing",
                "Quality Assessment",
                "Data Standardization",
            ],
            "capabilities": [
                "Individual Processing",
                "Discovery Flow Integration",
                "Quality Intelligence",
            ],
            "api_endpoints": [
                "/api/v1/flows/data-cleansing"
            ],  # NOTE: May need router verification
            "description": "Individual specialized agent from Discovery Flow Redesign",
            "status": "active",
            "source": "individual_flow_agents",
        },
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
                "health": (
                    "healthy" if individual_agent["status"] == "active" else "inactive"
                ),
            },
            "features": {
                "learning_enabled": True,
                "cross_page_communication": True,
                "modular_handlers": True,
            },
            "performance": {
                "tasks_completed": "N/A",
                "success_rate": "N/A",
                "avg_execution_time": "N/A",
            },
            "registration_time": datetime.utcnow().isoformat(),
            "last_heartbeat": datetime.utcnow().isoformat(),
        }

        if phase not in agent_details_by_phase:
            agent_details_by_phase[phase] = {
                "phase_name": phase.replace("_", " ").title(),
                "total_agents": 0,
                "active_agents": 0,
                "agents": [],
            }

        agent_details_by_phase[phase]["agents"].append(agent_info)
        agent_details_by_phase[phase]["total_agents"] += 1
        if individual_agent["status"] == "active":
            agent_details_by_phase[phase]["active_agents"] += 1


def _calculate_summary_statistics(agent_details_by_phase: dict) -> dict:
    """Calculate summary statistics for all agents."""
    all_agents = []
    for phase_data in agent_details_by_phase.values():
        if isinstance(phase_data, dict) and "agents" in phase_data:
            agents_list = phase_data["agents"]
            if isinstance(agents_list, list):
                all_agents.extend(agents_list)

    # Count agents by all possible statuses from AgentStatus enum
    status_counts = {
        "active": 0,
        "standby": 0,
        "busy": 0,
        "error": 0,
        "maintenance": 0,
        "planned": 0,
        "in_development": 0,
        "unknown": 0,  # For any unexpected statuses
    }

    for agent in all_agents:
        if isinstance(agent, dict):
            status_info = _safe_get_dict_value(agent, "status", {}, dict)
            current_status = _safe_get_dict_value(
                status_info, "current_status", "unknown", str
            )

            # Count by status, defaulting to 'unknown' for unexpected values
            if current_status in status_counts:
                status_counts[current_status] += 1
            else:
                status_counts["unknown"] += 1
                logger.warning(f"Unexpected agent status encountered: {current_status}")

    # Count feature usage with safe access
    feature_counts = {
        "learning_enabled": 0,
        "cross_page_communication": 0,
        "modular_handlers": 0,
    }

    for agent in all_agents:
        if isinstance(agent, dict):
            features = _safe_get_dict_value(agent, "features", {}, dict)
            for feature_name in feature_counts.keys():
                if _safe_get_dict_value(features, feature_name, False, bool):
                    feature_counts[feature_name] += 1

    return {
        "total_agents": len(all_agents),
        "by_phase": {
            phase: _safe_get_dict_value(data, "total_agents", 0, int)
            for phase, data in agent_details_by_phase.items()
            if isinstance(data, dict)
        },
        "by_status": status_counts,
        "features": feature_counts,
    }


def _process_single_crew(agent_details_by_phase: dict, crew_type: str, crew_factory):
    """Process a single crew type and add its agents."""
    try:
        crew_info = crew_factory.get_crew_info(crew_type)
        if not crew_info or not isinstance(crew_info, dict):
            logger.warning(f"Invalid or missing crew info for {crew_type}")
            return

        crew = crew_factory.create_crew(crew_type)
        if not crew:
            logger.warning(f"Could not create crew for {crew_type}")
            return

        try:
            sample_inputs = {"raw_data": [{"sample": "data"}]}
            crew.initialize_crew(sample_inputs)

            for i, agent in enumerate(crew.agents):
                agent_info, crew_phase = _create_crew_agent_info(
                    crew_type, crew_info, agent, i
                )

                # Add to appropriate phase
                if crew_phase not in agent_details_by_phase:
                    agent_details_by_phase[crew_phase] = {
                        "phase_name": crew_phase.replace("_", " ").title(),
                        "total_agents": 0,
                        "active_agents": 0,
                        "agents": [],
                    }

                agent_details_by_phase[crew_phase]["agents"].append(agent_info)
                agent_details_by_phase[crew_phase]["total_agents"] += 1
                agent_details_by_phase[crew_phase]["active_agents"] += 1

        except Exception as crew_init_error:
            logger.warning(
                f"Could not initialize crew {crew_type} for agent details: {crew_init_error}"
            )
            _add_fallback_agents(agent_details_by_phase, crew_type)
    except Exception as e:
        logger.warning(f"Error processing crew {crew_type}: {e}")


def _get_agents_from_phase2_crews(agent_details_by_phase: dict):
    """Get agents from Phase 2 crew system."""
    try:
        from app.services.crews.factory import CrewFactory

        available_crews = CrewFactory.list_crews()
        logger.info(f"Found {len(available_crews)} crew types from Phase 2 system")

        for crew_type in available_crews:
            _process_single_crew(agent_details_by_phase, crew_type, CrewFactory)

    except Exception as e:
        logger.warning(f"Phase 2 crew system not available: {e}")


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

        # Get status report once for all registry operations with validation
        raw_status_report = agent_monitor.get_status_report()
        status_report = _validate_status_report(raw_status_report)

        # 1. GET AGENTS FROM AGENT REGISTRY
        _get_agents_from_registry(agent_details_by_phase, status_report)

        # 2. GET AGENTS FROM PHASE 2 CREW SYSTEM
        _get_agents_from_phase2_crews(agent_details_by_phase)

        # 3. ADD INDIVIDUAL FLOW AGENTS
        _add_individual_flow_agents(agent_details_by_phase)

        # Calculate summary statistics
        summary = _calculate_summary_statistics(agent_details_by_phase)

        return {
            "success": True,
            "timestamp": "2025-01-28T12:00:00Z",
            "agents_by_phase": agent_details_by_phase,
            "summary": summary,
        }

    except Exception as e:
        logger.error(f"Error getting agent details: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent details: {str(e)}"
        )


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
                detail=f"Invalid phase. Valid phases are: {', '.join(valid_phases)}",
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
                "modular_handlers": agent.modular_handlers,
            }
            agents_list.append(agent_info)

        return {
            "success": True,
            "phase": phase.title(),
            "agents": agents_list,
            "count": len(agents_list),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agents by phase: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get agents by phase: {str(e)}"
        )


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
                    detail=f"Invalid status. Valid statuses are: {', '.join(valid_statuses)}",
                )

        agent_registry.update_agent_status(agent_id, **kwargs)

        return {
            "success": True,
            "agent_id": agent_id,
            "heartbeat_updated": True,
            "status_updated": status is not None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent heartbeat: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update agent heartbeat: {str(e)}"
        )


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
            "registry": registry_data,
        }

    except Exception as e:
        logger.error(f"Error exporting agent registry: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to export agent registry: {str(e)}"
        )
