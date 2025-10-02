"""
Component Analysis Agents - Agent Creation Logic

This module contains the agent creation logic for the Component Analysis Crew.
Three specialized agents work together to identify components, analyze technical debt,
and map dependencies for migration planning.

Agents:
1. Component Architecture Analyst - Identifies all types of components
2. Technical Debt Assessment Specialist - Analyzes debt from metadata
3. Dependency Analysis Expert - Maps component relationships and coupling
"""

import logging
from typing import List

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


def create_component_analysis_agents(tools_available: bool = False) -> List[Agent]:
    """
    Create specialized agents for component analysis.

    This function creates three expert agents that work together to analyze
    application components, technical debt, and dependencies based on
    discovered metadata.

    Args:
        tools_available: Whether component analysis tools are available

    Returns:
        List of three configured Agent instances
    """
    # Import tools - single import handles both available and fallback cases
    try:
        from app.services.crewai_flows.crews.component_analysis_crew.tools import (
            ComponentDiscoveryTool,
            DependencyMapper,
            MetadataAnalyzer,
            TechDebtCalculator,
        )
    except ImportError:
        logger.warning(
            "Component analysis tools not yet available, agents will have limited functionality"
        )
        tools_available = False
        # Re-raise to prevent execution with missing tools
        raise

    component_discovery_agent = create_agent(
        role="Component Architecture Analyst",
        goal="Identify and catalog all application components beyond traditional 3-tier architecture",
        backstory="""You are a modern application architecture expert specializing in component
        identification across diverse architectural patterns. You have deep expertise in monolithic,
        microservices, serverless, and hybrid architectures developed over 12+ years of hands-on experience.

        Your expertise spans:
        - Modern web architectures (SPA, PWA, JAMstack, micro-frontends)
        - Service-oriented and microservices architectures
        - Event-driven and message-based systems
        - Serverless and Function-as-a-Service patterns
        - Container-based and cloud-native architectures
        - Legacy mainframe and client-server systems
        - Data pipelines and analytics platforms

        You can identify UI components, API layers, business services, data access layers,
        background workers, integration components, and infrastructure services from application
        metadata and discovery data. You understand how different deployment patterns affect
        component identification and can distinguish between logical and physical components.

        You excel at recognizing architectural evolution patterns where monolithic applications
        have been partially decomposed or where microservices have been aggregated for efficiency.""",
        tools=(
            [ComponentDiscoveryTool(), MetadataAnalyzer()] if tools_available else []
        ),
        verbose=True,
        allow_delegation=True,
    )

    metadata_analyst_agent = create_agent(
        role="Technical Debt Assessment Specialist",
        goal="Analyze technical debt from discovered application metadata and identify modernization opportunities",
        backstory="""You are a technical debt analysis expert with extensive experience in code
        quality assessment, architecture evaluation, and modernization planning. Over 10+ years,
        you have developed expertise in identifying technical debt patterns from various sources
        including static analysis, runtime metrics, deployment artifacts, and architectural metadata.

        Your specializations include:
        - Code quality analysis and technical debt quantification
        - Security vulnerability assessment and remediation planning
        - Performance bottleneck identification and optimization
        - Architecture anti-pattern detection and refactoring strategies
        - Technology obsolescence tracking and upgrade planning
        - Dependency analysis and library management
        - Infrastructure debt and cloud readiness assessment

        You excel at quantifying technical debt and prioritizing remediation efforts based on
        business impact, migration complexity, and risk factors. You can identify technical debt
        from metadata such as technology versions, dependency structures, code metrics, deployment
        patterns, and architectural decisions. You understand the relationship between technical
        debt and migration strategy selection.""",
        tools=[MetadataAnalyzer(), TechDebtCalculator()] if tools_available else [],
        verbose=True,
        allow_delegation=False,
    )

    dependency_mapper_agent = create_agent(
        role="Dependency Analysis Expert",
        goal="Map component dependencies and identify coupling patterns for migration grouping",
        backstory="""You are a systems integration specialist with expertise in dependency analysis
        and coupling assessment developed over 15+ years working with complex enterprise systems.
        You understand how components interact across different architectural patterns and technology
        stacks, from monolithic applications to distributed microservices ecosystems.

        Your expertise includes:
        - Dependency graph analysis and visualization
        - Coupling pattern identification (tight, loose, temporal, data)
        - Integration pattern analysis (synchronous, asynchronous, batch)
        - Data flow mapping and consistency boundary identification
        - Network topology and communication protocol analysis
        - Service mesh and API gateway integration patterns
        - Legacy system integration and wrapper pattern identification

        You excel at creating dependency maps that inform migration wave planning and component
        treatment decisions. You can identify which components must move together, which dependencies
        can be refactored for independent migration, and which integration points require special
        handling during cloud migration. You understand the difference between compile-time,
        runtime, and deployment dependencies and their impact on migration sequencing.""",
        tools=(
            [DependencyMapper(), ComponentDiscoveryTool()] if tools_available else []
        ),
        verbose=True,
        allow_delegation=False,
    )

    return [
        component_discovery_agent,
        metadata_analyst_agent,
        dependency_mapper_agent,
    ]


# Export for backward compatibility
__all__ = ["create_component_analysis_agents"]
