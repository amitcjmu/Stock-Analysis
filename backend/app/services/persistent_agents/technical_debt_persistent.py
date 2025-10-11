"""
Persistent Technical Debt Analysis Agent Wrapper (ADR-015, ADR-024)

This module provides a persistent agent wrapper for technical debt analysis operations.
Replaces: app.services.crewai_flows.crews.technical_debt_crew
Replaces: app.services.crewai_flows.crews.tech_debt_analysis_crew

Architecture:
- Uses TenantScopedAgentPool for agent lifecycle management
- Single agent instance per (tenant, agent_type) - singleton pattern
- Memory managed by TenantMemoryManager (memory=False for crews per ADR-024)

Migration Context:
- Part of Workstream B, Phase B1: Create Persistent Agent Wrappers
- Task B1.3: Technical Debt Wrapper
- Created: 2025-10-11
"""

from typing import Any, Dict, List
import logging

from app.core.context import RequestContext
from app.services.service_registry import ServiceRegistry
from app.services.persistent_agents import TenantScopedAgentPool

logger = logging.getLogger(__name__)


async def get_persistent_tech_debt_analyzer(
    context: RequestContext,
    service_registry: ServiceRegistry,
) -> Any:
    """
    Get or create persistent technical debt analysis agent.

    This function replaces direct crew instantiation with persistent agent pattern.

    Args:
        context: Request context with client_account_id and engagement_id
        service_registry: Service registry for agent dependencies

    Returns:
        Persistent agent configured for technical debt analysis

    Example:
        >>> agent = await get_persistent_tech_debt_analyzer(context, service_registry)
        >>> result = await agent.process(codebase_data)

    Replaces:
        from app.services.crewai_flows.crews.technical_debt_crew import create_tech_debt_crew
        crew = create_tech_debt_crew(crewai_service, codebase_data)

    Architecture:
        - Singleton per (tenant, agent_type)
        - Lazy initialization
        - Memory=False (uses TenantMemoryManager per ADR-024)
    """
    logger.info(
        f"Getting persistent technical debt analysis agent for "
        f"client_account_id={context.client_account_id}, "
        f"engagement_id={context.engagement_id}"
    )

    agent = await TenantScopedAgentPool.get_agent(
        context=context,
        agent_type="tech_debt_analysis",
        service_registry=service_registry,
    )

    logger.debug(
        f"✅ Persistent technical debt analysis agent retrieved: {type(agent).__name__}"
    )
    return agent


async def execute_tech_debt_analysis(
    context: RequestContext,
    service_registry: ServiceRegistry,
    applications: List[Dict[str, Any]],
    analysis_scope: str = "comprehensive",  # "comprehensive", "security", "performance", "maintainability"
    include_recommendations: bool = True,
    severity_threshold: str = "medium",  # "low", "medium", "high", "critical"
    **kwargs,
) -> Dict[str, Any]:
    """
    Execute technical debt analysis using persistent agent.

    High-level convenience function that gets the agent and processes data
    in a single call.

    Args:
        context: Request context
        service_registry: Service registry
        applications: List of applications to analyze for technical debt
        analysis_scope: Scope of analysis ("comprehensive", "security", "performance", "maintainability")
        include_recommendations: Whether to include remediation recommendations
        severity_threshold: Minimum severity level to report ("low", "medium", "high", "critical")
        **kwargs: Additional parameters passed to agent.process()

    Returns:
        Dict containing:
            - tech_debt_items: List of identified technical debt items
            - severity_distribution: Distribution of debt by severity
            - total_estimated_cost: Estimated cost to address all debt
            - recommendations: Prioritized remediation recommendations
            - risk_assessment: Risk assessment for each debt item
            - metadata: Processing metadata

    Example:
        >>> result = await execute_tech_debt_analysis(
        ...     context=context,
        ...     service_registry=service_registry,
        ...     applications=[
        ...         {"name": "LegacyApp", "language": "java", "lines_of_code": 50000}
        ...     ],
        ...     analysis_scope="comprehensive",
        ...     severity_threshold="high"
        ... )
        >>> print(result["tech_debt_items"])
        [
            {
                "type": "outdated_dependencies",
                "severity": "high",
                "description": "Java 8 EOL - upgrade to Java 17",
                "estimated_effort": "80 hours"
            },
            {
                "type": "security_vulnerability",
                "severity": "critical",
                "description": "SQL injection risk in user input handling",
                "estimated_effort": "24 hours"
            }
        ]

    Replaces:
        from app.services.crewai_flows.crews.technical_debt_crew import create_tech_debt_crew
        crew = create_tech_debt_crew(crewai_service, applications)
        result = crew.kickoff()
    """
    logger.info(
        f"Executing technical debt analysis for {len(applications)} applications "
        f"(scope={analysis_scope}, threshold={severity_threshold}, "
        f"client_account_id={context.client_account_id})"
    )

    # Get persistent agent
    agent = await get_persistent_tech_debt_analyzer(context, service_registry)

    # Prepare input data
    input_data = {
        "applications": applications,
        "analysis_scope": analysis_scope,
        "include_recommendations": include_recommendations,
        "severity_threshold": severity_threshold,
        **kwargs,
    }

    # Execute technical debt analysis
    try:
        result = await agent.process(input_data)
        logger.info(
            f"✅ Technical debt analysis completed: "
            f"{len(result.get('tech_debt_items', []))} items identified, "
            f"total estimated cost: {result.get('total_estimated_cost', 'unknown')}"
        )
        return result
    except Exception as e:
        logger.error(f"❌ Technical debt analysis failed: {e}", exc_info=True)
        raise


async def analyze_security_debt(
    context: RequestContext,
    service_registry: ServiceRegistry,
    applications: List[Dict[str, Any]],
    **kwargs,
) -> Dict[str, Any]:
    """
    Convenience function for security-focused technical debt analysis.

    Executes technical debt analysis focused on security vulnerabilities,
    outdated security patches, insecure configurations, etc.

    Args:
        context: Request context
        service_registry: Service registry
        applications: List of applications to analyze
        **kwargs: Additional parameters

    Returns:
        Technical debt analysis results focused on security issues

    Example:
        >>> result = await analyze_security_debt(
        ...     context=context,
        ...     service_registry=service_registry,
        ...     applications=apps_list
        ... )
    """
    return await execute_tech_debt_analysis(
        context=context,
        service_registry=service_registry,
        applications=applications,
        analysis_scope="security",
        **kwargs,
    )


async def analyze_performance_debt(
    context: RequestContext,
    service_registry: ServiceRegistry,
    applications: List[Dict[str, Any]],
    **kwargs,
) -> Dict[str, Any]:
    """
    Convenience function for performance-focused technical debt analysis.

    Executes technical debt analysis focused on performance issues,
    inefficient algorithms, resource bottlenecks, etc.

    Args:
        context: Request context
        service_registry: Service registry
        applications: List of applications to analyze
        **kwargs: Additional parameters

    Returns:
        Technical debt analysis results focused on performance issues

    Example:
        >>> result = await analyze_performance_debt(
        ...     context=context,
        ...     service_registry=service_registry,
        ...     applications=apps_list
        ... )
    """
    return await execute_tech_debt_analysis(
        context=context,
        service_registry=service_registry,
        applications=applications,
        analysis_scope="performance",
        **kwargs,
    )


async def analyze_maintainability_debt(
    context: RequestContext,
    service_registry: ServiceRegistry,
    applications: List[Dict[str, Any]],
    **kwargs,
) -> Dict[str, Any]:
    """
    Convenience function for maintainability-focused technical debt analysis.

    Executes technical debt analysis focused on code maintainability issues,
    code smells, complexity, documentation gaps, etc.

    Args:
        context: Request context
        service_registry: Service registry
        applications: List of applications to analyze
        **kwargs: Additional parameters

    Returns:
        Technical debt analysis results focused on maintainability issues

    Example:
        >>> result = await analyze_maintainability_debt(
        ...     context=context,
        ...     service_registry=service_registry,
        ...     applications=apps_list
        ... )
    """
    return await execute_tech_debt_analysis(
        context=context,
        service_registry=service_registry,
        applications=applications,
        analysis_scope="maintainability",
        **kwargs,
    )


# Backward compatibility alias
async def create_persistent_tech_debt_analyzer(
    context: RequestContext,
    service_registry: ServiceRegistry,
) -> Any:
    """
    Backward compatibility alias for get_persistent_tech_debt_analyzer().

    Deprecated: Use get_persistent_tech_debt_analyzer() instead.
    """
    logger.warning(
        "create_persistent_tech_debt_analyzer() is deprecated. "
        "Use get_persistent_tech_debt_analyzer() instead."
    )
    return await get_persistent_tech_debt_analyzer(context, service_registry)
