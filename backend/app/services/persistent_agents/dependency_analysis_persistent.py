"""
Persistent Dependency Analysis Agent Wrapper (ADR-015, ADR-024)

This module provides a persistent agent wrapper for dependency analysis operations.
Replaces: app.services.crewai_flows.crews.dependency_analysis_crew

Architecture:
- Uses TenantScopedAgentPool for agent lifecycle management
- Single agent instance per (tenant, agent_type) - singleton pattern
- Memory managed by TenantMemoryManager (memory=False for crews per ADR-024)

Migration Context:
- Part of Workstream B, Phase B1: Create Persistent Agent Wrappers
- Task B1.2: Dependency Analysis Wrapper
- Created: 2025-10-11
"""

from typing import Any, Dict, List
import logging

from app.core.context import RequestContext
from app.services.service_registry import ServiceRegistry
from app.services.persistent_agents import TenantScopedAgentPool

logger = logging.getLogger(__name__)


async def get_persistent_dependency_analyzer(
    context: RequestContext,
    service_registry: ServiceRegistry,
) -> Any:
    """
    Get or create persistent dependency analysis agent.

    This function replaces direct crew instantiation with persistent agent pattern.

    Args:
        context: Request context with client_account_id and engagement_id
        service_registry: Service registry for agent dependencies

    Returns:
        Persistent agent configured for dependency analysis

    Example:
        >>> agent = await get_persistent_dependency_analyzer(context, service_registry)
        >>> result = await agent.process(applications_data)

    Replaces:
        from app.services.crewai_flows.crews.dependency_analysis_crew import create_dependency_crew
        crew = create_dependency_crew(crewai_service, applications)

    Architecture:
        - Singleton per (tenant, agent_type)
        - Lazy initialization
        - Memory=False (uses TenantMemoryManager per ADR-024)
    """
    logger.info(
        f"Getting persistent dependency analysis agent for "
        f"client_account_id={context.client_account_id}, "
        f"engagement_id={context.engagement_id}"
    )

    agent = await TenantScopedAgentPool.get_agent(
        context=context,
        agent_type="dependency_analysis",
        service_registry=service_registry,
    )

    logger.debug(
        f"✅ Persistent dependency analysis agent retrieved: {type(agent).__name__}"
    )
    return agent


async def execute_dependency_analysis(
    context: RequestContext,
    service_registry: ServiceRegistry,
    applications: List[Dict[str, Any]],
    analysis_type: str = "full",  # "full", "app_to_app", "app_to_server"
    include_transitive: bool = True,
    **kwargs,
) -> Dict[str, Any]:
    """
    Execute dependency analysis using persistent agent.

    High-level convenience function that gets the agent and processes data
    in a single call.

    Args:
        context: Request context
        service_registry: Service registry
        applications: List of applications to analyze dependencies for
        analysis_type: Type of dependency analysis ("full", "app_to_app", "app_to_server")
        include_transitive: Whether to include transitive dependencies
        **kwargs: Additional parameters passed to agent.process()

    Returns:
        Dict containing:
            - dependencies: List of discovered dependencies
            - dependency_graph: Graph representation of dependencies
            - critical_dependencies: Dependencies flagged as critical
            - recommendations: Migration recommendations based on dependencies
            - metadata: Processing metadata

    Example:
        >>> result = await execute_dependency_analysis(
        ...     context=context,
        ...     service_registry=service_registry,
        ...     applications=[
        ...         {"name": "CustomerPortal", "type": "web"},
        ...         {"name": "OrderService", "type": "api"}
        ...     ],
        ...     analysis_type="app_to_app"
        ... )
        >>> print(result["dependencies"])
        [
            {
                "source": "CustomerPortal",
                "target": "OrderService",
                "type": "api_call",
                "criticality": "high"
            }
        ]

    Replaces:
        from app.services.crewai_flows.crews.dependency_analysis_crew import create_dependency_crew
        crew = create_dependency_crew(crewai_service, applications)
        result = crew.kickoff()
    """
    logger.info(
        f"Executing dependency analysis for {len(applications)} applications "
        f"(type={analysis_type}, transitive={include_transitive}, "
        f"client_account_id={context.client_account_id})"
    )

    # Get persistent agent
    agent = await get_persistent_dependency_analyzer(context, service_registry)

    # Prepare input data
    input_data = {
        "applications": applications,
        "analysis_type": analysis_type,
        "include_transitive": include_transitive,
        **kwargs,
    }

    # Execute dependency analysis
    try:
        result = await agent.process(input_data)
        logger.info(
            f"✅ Dependency analysis completed: "
            f"{len(result.get('dependencies', []))} dependencies found, "
            f"{len(result.get('critical_dependencies', []))} critical"
        )
        return result
    except Exception as e:
        logger.error(f"❌ Dependency analysis failed: {e}", exc_info=True)
        raise


async def analyze_app_to_app_dependencies(
    context: RequestContext,
    service_registry: ServiceRegistry,
    applications: List[Dict[str, Any]],
    **kwargs,
) -> Dict[str, Any]:
    """
    Convenience function for app-to-app dependency analysis.

    Executes dependency analysis focused on application-to-application
    relationships (API calls, message queues, shared databases, etc.)

    Args:
        context: Request context
        service_registry: Service registry
        applications: List of applications to analyze
        **kwargs: Additional parameters

    Returns:
        Dependency analysis results focused on app-to-app relationships

    Example:
        >>> result = await analyze_app_to_app_dependencies(
        ...     context=context,
        ...     service_registry=service_registry,
        ...     applications=apps_list
        ... )
    """
    return await execute_dependency_analysis(
        context=context,
        service_registry=service_registry,
        applications=applications,
        analysis_type="app_to_app",
        **kwargs,
    )


async def analyze_app_to_server_dependencies(
    context: RequestContext,
    service_registry: ServiceRegistry,
    applications: List[Dict[str, Any]],
    **kwargs,
) -> Dict[str, Any]:
    """
    Convenience function for app-to-server dependency analysis.

    Executes dependency analysis focused on application-to-server
    relationships (database servers, web servers, app servers, etc.)

    Args:
        context: Request context
        service_registry: Service registry
        applications: List of applications to analyze
        **kwargs: Additional parameters

    Returns:
        Dependency analysis results focused on app-to-server relationships

    Example:
        >>> result = await analyze_app_to_server_dependencies(
        ...     context=context,
        ...     service_registry=service_registry,
        ...     applications=apps_list
        ... )
    """
    return await execute_dependency_analysis(
        context=context,
        service_registry=service_registry,
        applications=applications,
        analysis_type="app_to_server",
        **kwargs,
    )


# Backward compatibility alias
async def create_persistent_dependency_analyzer(
    context: RequestContext,
    service_registry: ServiceRegistry,
) -> Any:
    """
    Backward compatibility alias for get_persistent_dependency_analyzer().

    Deprecated: Use get_persistent_dependency_analyzer() instead.
    """
    logger.warning(
        "create_persistent_dependency_analyzer() is deprecated. "
        "Use get_persistent_dependency_analyzer() instead."
    )
    return await get_persistent_dependency_analyzer(context, service_registry)
