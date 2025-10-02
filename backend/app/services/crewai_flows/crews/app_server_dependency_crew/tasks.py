"""
App-Server Dependency Tasks - Task Creation and Crew Assembly Logic

This module contains task creation logic and crew factory functions for the
App-Server Dependency Crew. It defines the workflow for dependency mapping,
hosting analysis, and migration impact assessment.

Tasks:
1. Planning Task - Strategic dependency analysis planning
2. Hosting Discovery Task - Map application-to-server relationships
3. Impact Assessment Task - Analyze migration complexity and risks
"""

import logging
from typing import Any, Dict, List

from crewai import Crew, Process

from app.services.crewai_flows.config.crew_factory import create_crew, create_task

logger = logging.getLogger(__name__)

# Import advanced CrewAI features with fallbacks
try:
    from crewai.knowledge.knowledge import Knowledge
    from crewai.memory import LongTermMemory

    CREWAI_ADVANCED_AVAILABLE = True
except ImportError:
    CREWAI_ADVANCED_AVAILABLE = False

    # Fallback classes
    class LongTermMemory:
        def __init__(self, **kwargs):
            pass

    class Knowledge:
        def __init__(self, **kwargs):
            pass


# CrewAI Agent and Task types
try:
    from crewai import Agent, Task

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = object  # type: ignore[misc, assignment]
    Task = object  # type: ignore[misc, assignment]


def create_app_server_dependency_tasks(
    agents: List[Agent], asset_inventory: Dict[str, Any]
) -> List[Task]:
    """
    Create hierarchical tasks for app-server dependency analysis.

    Args:
        agents: List of three agents [manager, hosting_expert, migration_analyst]
        asset_inventory: Dictionary containing servers and applications inventory

    Returns:
        List of three configured Task instances
    """
    manager, hosting_expert, migration_impact_analyst = agents

    servers = asset_inventory.get("servers", [])
    applications = asset_inventory.get("applications", [])

    # Import tools for task assignment
    try:
        from app.services.crewai_flows.crews.app_server_dependency_crew.tools import (
            _create_capacity_analysis_tool,
            _create_hosting_analysis_tool,
            _create_migration_complexity_tool,
            _create_topology_mapping_tool,
        )

        hosting_tools = [
            _create_hosting_analysis_tool(asset_inventory),
            _create_topology_mapping_tool(),
        ]

        impact_tools = [
            _create_migration_complexity_tool(asset_inventory),
            _create_capacity_analysis_tool(),
        ]
    except ImportError:
        logger.warning("Tools not available, tasks will operate without tools")
        hosting_tools = []
        impact_tools = []

    # Planning Task - Manager coordinates dependency analysis approach
    planning_task = create_task(
        description=f"""Plan comprehensive app-server dependency analysis strategy.

        Available assets for analysis:
        - Servers: {len(servers)} identified server assets
        - Applications: {len(applications)} identified application assets

        Create a dependency analysis plan that:
        1. Assigns hosting relationship discovery priorities
        2. Defines dependency mapping methodology
        3. Establishes migration impact assessment criteria
        4. Plans collaboration between hosting and impact specialists
        5. Leverages inventory insights from shared memory

        Use your planning capabilities to coordinate comprehensive dependency mapping.""",
        expected_output=(
            "Comprehensive dependency analysis execution plan with hosting discovery "
            "strategy and impact assessment approach"
        ),
        agent=manager,
        tools=[],
    )

    # Hosting Relationship Discovery Task
    hosting_discovery_task = create_task(
        description=f"""Identify and map application-to-server hosting relationships.

        Assets to analyze:
        - Server inventory: {len(servers)} servers
        - Application inventory: {len(applications)} applications
        - Sample servers: {servers[:3] if servers else []}
        - Sample applications: {applications[:3] if applications else []}

        Hosting Analysis Requirements:
        1. Map applications to their hosting servers
        2. Identify virtual machine and container relationships
        3. Determine database hosting patterns
        4. Map web application server dependencies
        5. Identify shared hosting platforms
        6. Generate hosting relationship matrix
        7. Store hosting insights in shared memory for impact analysis

        Collaborate with migration impact analyst to share hosting discoveries.""",
        expected_output="Comprehensive hosting relationship matrix with app-server mappings and hosting patterns",
        agent=hosting_expert,
        context=[planning_task],
        tools=hosting_tools,
    )

    # Migration Impact Assessment Task
    impact_assessment_task = create_task(
        description=f"""Assess migration complexity and risk based on hosting dependencies.

        Hosting relationships: Use insights from hosting expert
        Server inventory: {len(servers)} servers with hosting dependencies
        Application inventory: {len(applications)} applications with hosting requirements

        Impact Analysis Requirements:
        1. Assess migration complexity for each hosting relationship
        2. Identify single points of failure in hosting patterns
        3. Determine migration sequencing requirements
        4. Evaluate infrastructure consolidation opportunities
        5. Assess cloud readiness based on hosting patterns
        6. Generate migration risk assessment
        7. Use hosting expert insights from shared memory

        Collaborate with hosting expert to validate impact assessments.""",
        expected_output="Comprehensive migration impact assessment with complexity scoring and risk analysis",
        agent=migration_impact_analyst,
        context=[hosting_discovery_task],
        tools=impact_tools,
    )

    return [planning_task, hosting_discovery_task, impact_assessment_task]


def create_app_server_dependency_crew_instance(
    crewai_service,
    asset_inventory: Dict[str, Any],
    shared_memory=None,
) -> Crew:
    """
    Create enhanced App-Server Dependency Crew with inventory intelligence.

    This is the main factory function for creating the crew instance.
    Uses asset inventory insights from shared memory to map hosting relationships.

    Args:
        crewai_service: Service providing LLM configuration
        asset_inventory: Dictionary containing servers and applications
        shared_memory: Optional shared memory for cross-crew collaboration

    Returns:
        Configured Crew instance ready for execution

    Raises:
        Exception: If crew creation fails, returns fallback crew
    """
    # Access inventory insights from shared memory
    if shared_memory:
        logger.info(
            "🧠 App-Server Dependency Crew accessing asset inventory insights from shared memory"
        )

    try:
        # Get proper LLM configuration
        try:
            from app.services.llm_config import get_crewai_llm

            llm_model = get_crewai_llm()
            logger.info(
                "✅ Using configured DeepInfra LLM for App-Server Dependency Crew"
            )
        except Exception as e:
            logger.warning(f"Failed to get configured LLM, using fallback: {e}")
            llm_model = getattr(crewai_service, "llm", None)

        # Import agent and task creation functions
        from app.services.crewai_flows.crews.app_server_dependency_crew.agents import (
            create_app_server_dependency_agents,
        )

        # Create agents with tools
        agents = create_app_server_dependency_agents(
            llm_model=llm_model,
            shared_memory=shared_memory,
            knowledge_base=None,
            asset_inventory=asset_inventory,
            tools_available=True,
        )

        # Create tasks
        tasks = create_app_server_dependency_tasks(agents, asset_inventory)

        # Use hierarchical process if advanced features available
        process = (
            Process.hierarchical if CREWAI_ADVANCED_AVAILABLE else Process.sequential
        )

        crew_config = {
            "agents": agents,
            "tasks": tasks,
            "process": process,
            "verbose": True,
            "max_iterations": 10,  # Limit total crew iterations
            "step_callback": lambda step: logger.info(f"Crew step {step}"),
        }

        # Add advanced features if available
        if CREWAI_ADVANCED_AVAILABLE:
            # Ensure manager_llm uses our configured LLM and not gpt-4o-mini
            crew_config.update(
                {
                    "manager_llm": llm_model,  # Critical: Use our DeepInfra LLM
                    "planning": True,
                    "planning_llm": llm_model,  # Force planning to use our LLM too
                    "memory": False,  # Per ADR-024: Use TenantMemoryManager for enterprise memory
                    "knowledge": None,
                    "share_crew": True,
                    "collaboration": True,
                }
            )

            # Additional environment override to prevent any gpt-4o-mini fallback
            import os

            os.environ["OPENAI_MODEL_NAME"] = (
                str(llm_model)
                if isinstance(llm_model, str)
                else "deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
            )

        logger.info(
            f"Creating App-Server Dependency Crew with "
            f"{process.name if hasattr(process, 'name') else 'sequential'} process"
        )
        logger.info(
            f"Using LLM: {llm_model if isinstance(llm_model, str) else 'Unknown'}"
        )

        crew = create_crew(**crew_config)
        logger.info(
            "✅ Enhanced App-Server Dependency Crew created with inventory intelligence"
        )
        return crew

    except Exception as e:
        logger.error(f"Failed to create enhanced App-Server Dependency Crew: {e}")
        # Import and use fallback
        from app.services.crewai_flows.crews.app_server_dependency_crew.crew import (
            AppServerDependencyCrew,
        )

        crew_instance = AppServerDependencyCrew(
            crewai_service, shared_memory=shared_memory
        )
        return crew_instance.create_crew(asset_inventory)


# Export for backward compatibility
__all__ = [
    "create_app_server_dependency_tasks",
    "create_app_server_dependency_crew_instance",
]
