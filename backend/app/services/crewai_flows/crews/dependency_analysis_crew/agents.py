"""
Dependency Analysis Agents - Agent Creation Logic

This module contains the agent creation logic for the Dependency Analysis Crew.
Three specialized agents work together to analyze network dependencies, application
dependencies, and infrastructure dependencies for migration planning.

Agents:
1. Network Architecture Specialist - Analyzes network topology and connectivity patterns
2. Application Dependency Analyst - Identifies application-to-application dependencies
3. Infrastructure Dependency Mapper - Maps infrastructure dependencies and migration paths
"""

import logging
from typing import List

from app.services.crewai_flows.config.crew_factory import create_agent
from app.services.crewai_flows.crews.dependency_analysis_crew.tools import (
    NetworkTopologyTool,
)

logger = logging.getLogger(__name__)

# CrewAI Agent type - imported conditionally
try:
    from crewai import Agent

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Fallback for type hints
    Agent = object  # type: ignore[misc, assignment]


def create_network_architecture_specialist(
    network_topology_tool: NetworkTopologyTool,
) -> Agent:
    """
    Create the Network Architecture Specialist agent.

    This agent specializes in analyzing network topology and architecture patterns
    to identify connectivity dependencies and migration requirements.

    Args:
        network_topology_tool: Tool for network topology analysis

    Returns:
        Configured Agent instance for network architecture analysis
    """
    # Get LLM configuration
    from app.services.llm_config import get_crewai_llm

    llm = get_crewai_llm()

    return create_agent(
        role="Network Architecture Specialist",
        goal="Analyze network topology and architecture patterns to identify connectivity "
        "dependencies and migration requirements",
        backstory="""You are a network architecture specialist with extensive experience in
        enterprise network design and migration planning. You understand complex network
        topologies, connectivity patterns, and the dependencies between network components.
        Your expertise helps identify critical network paths and potential migration
        challenges.""",
        tools=[network_topology_tool],
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        llm=llm,
    )


def create_application_dependency_analyst() -> Agent:
    """
    Create the Application Dependency Analyst agent.

    This agent specializes in analyzing application-to-application dependencies
    and integration patterns to identify how applications communicate and depend
    on each other.

    Returns:
        Configured Agent instance for application dependency analysis
    """
    # Get LLM configuration
    from app.services.llm_config import get_crewai_llm

    llm = get_crewai_llm()

    return create_agent(
        role="Application Dependency Analyst",
        goal="Analyze application-to-application dependencies and integration patterns",
        backstory="""You are an application dependency expert who understands how applications
        communicate, share data, and depend on each other in enterprise environments.
        You excel at identifying API integrations, data flows, and service dependencies.""",
        tools=[],
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        llm=llm,
    )


def create_infrastructure_dependency_mapper() -> Agent:
    """
    Create the Infrastructure Dependency Mapper agent.

    This agent specializes in mapping infrastructure dependencies and identifying
    critical migration paths based on network and application analysis.

    Returns:
        Configured Agent instance for infrastructure dependency mapping
    """
    # Get LLM configuration
    from app.services.llm_config import get_crewai_llm

    llm = get_crewai_llm()

    return create_agent(
        role="Infrastructure Dependency Mapper",
        goal="Map infrastructure dependencies and identify critical migration paths",
        backstory="""You are an infrastructure dependency specialist who maps out
        the relationships between applications and their underlying infrastructure.
        You understand server dependencies, database connections, and storage requirements.""",
        tools=[],
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        llm=llm,
    )


def create_dependency_analysis_agents(
    network_topology_tool: NetworkTopologyTool,
) -> List[Agent]:
    """
    Create all specialized agents for dependency analysis.

    This factory function creates the three expert agents that work together
    to analyze dependencies for migration planning.

    Args:
        network_topology_tool: Tool for network topology analysis

    Returns:
        List of three configured Agent instances
    """
    return [
        create_network_architecture_specialist(network_topology_tool),
        create_application_dependency_analyst(),
        create_infrastructure_dependency_mapper(),
    ]


# Export agent creation functions
__all__ = [
    "create_network_architecture_specialist",
    "create_application_dependency_analyst",
    "create_infrastructure_dependency_mapper",
    "create_dependency_analysis_agents",
]
