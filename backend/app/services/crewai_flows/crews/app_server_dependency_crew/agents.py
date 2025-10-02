"""
App-Server Dependency Agents - Agent Creation Logic

This module contains the agent creation logic for the App-Server Dependency Crew.
Three specialized agents work together to map hosting relationships, analyze
migration impact, and coordinate comprehensive dependency analysis.

Agents:
1. Dependency Manager - Coordinates comprehensive dependency mapping (with delegation)
2. Hosting Relationship Expert - Maps app-to-server hosting relationships
3. Migration Impact Analyst - Assesses migration complexity and risk
"""

import logging
from typing import Any, Dict, List, Optional

from app.services.crewai_flows.config.crew_factory import create_agent

logger = logging.getLogger(__name__)

# CrewAI Agent type - imported conditionally
try:
    from crewai import Agent

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Fallback for type hints
    Agent = object  # type: ignore[misc, assignment]

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


def create_app_server_dependency_agents(
    llm_model: Any,
    shared_memory: Optional[LongTermMemory] = None,
    knowledge_base: Optional[Knowledge] = None,
    asset_inventory: Optional[Dict[str, Any]] = None,
    tools_available: bool = False,
) -> List[Agent]:
    """
    Create specialized agents for app-server dependency analysis.

    This function creates three expert agents that work together to analyze
    hosting relationships, assess migration impact, and coordinate dependency mapping.

    Args:
        llm_model: The language model to use for agents
        shared_memory: Optional shared memory for cross-agent collaboration
        knowledge_base: Optional knowledge base for dependency patterns
        asset_inventory: Optional asset inventory for tool initialization
        tools_available: Whether dependency analysis tools are available

    Returns:
        List of three configured Agent instances
    """
    # Import tools if available
    if tools_available and asset_inventory:
        try:
            from app.services.crewai_flows.crews.app_server_dependency_crew.tools import (
                _create_capacity_analysis_tool,
                _create_hosting_analysis_tool,
                _create_impact_assessment_tool,
                _create_migration_complexity_tool,
                _create_relationship_validation_tool,
                _create_topology_mapping_tool,
            )

            hosting_tools = [
                _create_hosting_analysis_tool(asset_inventory),
                _create_topology_mapping_tool(),
                _create_relationship_validation_tool(),
            ]

            impact_tools = [
                _create_migration_complexity_tool(asset_inventory),
                _create_capacity_analysis_tool(),
                _create_impact_assessment_tool(),
            ]
        except ImportError:
            logger.warning(
                "App-server dependency tools not yet available, agents will have limited functionality"
            )
            hosting_tools = []
            impact_tools = []
    else:
        hosting_tools = []
        impact_tools = []

    # Get optimized agent configuration
    try:
        from app.services.crewai_flows.crews.crew_config import (
            get_optimized_agent_config,
        )

        manager_config = get_optimized_agent_config(allow_delegation=True)
        specialist_config = get_optimized_agent_config(allow_delegation=False)
    except ImportError:
        logger.warning("Using default agent configuration")
        manager_config = {"allow_delegation": True}
        specialist_config = {"allow_delegation": False}

    # Manager Agent for dependency coordination
    dependency_manager = create_agent(
        role="Dependency Analysis Manager",
        goal="Coordinate comprehensive app-server hosting relationship mapping for migration planning",
        backstory="""You are a systems architect with expertise in enterprise application hosting
        and dependency mapping. You excel at coordinating dependency analysis across complex
        enterprise environments and ensuring comprehensive hosting relationship discovery.

        With over 15 years of experience, you have managed hosting relationships across:
        - Traditional physical server environments
        - Virtualized data centers with VMware and Hyper-V
        - Container orchestration platforms (Kubernetes, Docker Swarm)
        - Cloud-native architectures (AWS, Azure, GCP)
        - Hybrid cloud and multi-cloud deployments
        - Legacy mainframe and midrange systems

        You are skilled at delegating specialized analysis tasks to hosting and migration experts
        while maintaining overall coordination and ensuring comprehensive dependency mapping.""",
        llm=llm_model,
        memory=shared_memory,
        knowledge=knowledge_base,
        verbose=True,
        planning=True if CREWAI_ADVANCED_AVAILABLE else False,
        **manager_config,
    )

    # Hosting Relationship Expert - specialist agent (no delegation)
    hosting_expert = create_agent(
        role="Hosting Relationship Expert",
        goal="Identify and map application-to-server hosting relationships with migration impact analysis",
        backstory="""You are an expert in application hosting with deep knowledge of enterprise
        infrastructure dependencies. You excel at identifying which applications run on which
        servers and understanding the hosting implications for migration planning.

        Your 12+ years of expertise spans:
        - Application server architectures (WebSphere, WebLogic, JBoss, Tomcat, IIS)
        - Database hosting patterns (Oracle RAC, SQL Server clusters, MongoDB replica sets)
        - Web application hosting (Apache, Nginx, load balancers)
        - Container hosting (Docker, Kubernetes, OpenShift)
        - Serverless and Function-as-a-Service patterns
        - Virtual machine and hypervisor configurations
        - Network topology and security zone mapping

        You understand how deployment patterns affect hosting relationships and can distinguish
        between logical and physical hosting dependencies. You excel at identifying shared hosting
        platforms, single points of failure, and consolidation opportunities.""",
        llm=llm_model,
        memory=shared_memory,
        knowledge=knowledge_base,
        verbose=True,
        collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
        tools=hosting_tools,
        **specialist_config,
    )

    # Migration Impact Analyst - specialist agent (no delegation)
    migration_impact_analyst = create_agent(
        role="Migration Impact Analyst",
        goal="Assess migration complexity and risk based on app-server dependencies",
        backstory="""You are a migration specialist with extensive experience in assessing the
        impact of hosting relationships on migration projects. You excel at identifying migration
        risks, complexity factors, and sequencing requirements based on dependencies.

        Your 10+ years of specialization includes:
        - Migration complexity assessment and effort estimation
        - Dependency analysis and critical path identification
        - Risk assessment for application and infrastructure migration
        - Cloud readiness evaluation and gap analysis
        - Refactoring vs. rehosting decision frameworks
        - Migration wave planning and sequencing strategies
        - Capacity planning and resource optimization

        You understand the relationship between hosting patterns and migration strategies (6R framework).
        You can identify which applications are candidates for lift-and-shift, which require refactoring,
        and which dependencies must be addressed before migration. You excel at quantifying migration
        complexity and creating actionable remediation roadmaps.""",
        llm=llm_model,
        memory=shared_memory,
        knowledge=knowledge_base,
        verbose=True,
        collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
        tools=impact_tools,
        **specialist_config,
    )

    return [dependency_manager, hosting_expert, migration_impact_analyst]


# Export for backward compatibility
__all__ = ["create_app_server_dependency_agents"]
