"""
Persistent Field Mapping Agent Wrapper (ADR-015, ADR-024)

This module provides a persistent agent wrapper for field mapping operations.
Replaces: app.services.crewai_flows.crews.field_mapping_crew.create_field_mapping_crew

Architecture:
- Uses TenantScopedAgentPool for agent lifecycle management
- Single agent instance per (tenant, agent_type) - singleton pattern
- Memory managed by TenantMemoryManager (memory=False for crews per ADR-024)

Migration Context:
- Part of Workstream B, Phase B1: Create Persistent Agent Wrappers
- Task B1.1: Field Mapping Wrapper
- Created: 2025-10-11
"""

from typing import Any, Dict, List, Optional
import logging

from app.core.context import RequestContext
from app.services.service_registry import ServiceRegistry
from app.services.persistent_agents import TenantScopedAgentPool

logger = logging.getLogger(__name__)


async def get_persistent_field_mapper(
    context: RequestContext,
    service_registry: ServiceRegistry,
) -> Any:
    """
    Get or create persistent field mapping agent.

    This function replaces direct crew instantiation with persistent agent pattern.

    Args:
        context: Request context with client_account_id and engagement_id
        service_registry: Service registry for agent dependencies

    Returns:
        Persistent agent configured for field mapping

    Example:
        >>> agent = await get_persistent_field_mapper(context, service_registry)
        >>> result = await agent.process(raw_data)

    Replaces:
        from app.services.crewai_flows.crews.field_mapping_crew import create_field_mapping_crew
        crew = create_field_mapping_crew(crewai_service, raw_data)

    Architecture:
        - Singleton per (tenant, agent_type)
        - Lazy initialization
        - Memory=False (uses TenantMemoryManager per ADR-024)
    """
    logger.info(
        f"Getting persistent field mapping agent for "
        f"client_account_id={context.client_account_id}, "
        f"engagement_id={context.engagement_id}"
    )

    agent = await TenantScopedAgentPool.get_agent(
        context=context,
        agent_type="field_mapper",  # Fixed: Must match agent_configuration.py (ADR-015)
        service_registry=service_registry,
    )

    logger.debug(f"✅ Persistent field mapping agent retrieved: {type(agent).__name__}")
    return agent


async def execute_field_mapping(
    context: RequestContext,
    service_registry: ServiceRegistry,
    raw_data: List[Dict[str, Any]],
    target_schema: Optional[Dict[str, Any]] = None,
    confidence_threshold: float = 0.7,
    **kwargs,
) -> Dict[str, Any]:
    """
    Execute field mapping using persistent agent.

    High-level convenience function that gets the agent and processes data
    in a single call.

    Args:
        context: Request context
        service_registry: Service registry
        raw_data: Raw data to map
        target_schema: Optional target schema for mapping
        confidence_threshold: Minimum confidence score for mappings (default: 0.7)
        **kwargs: Additional parameters passed to agent.process()

    Returns:
        Dict containing:
            - mapped_fields: List of field mappings
            - confidence_scores: Mapping confidence scores
            - unmapped_fields: Fields that couldn't be mapped
            - metadata: Processing metadata

    Example:
        >>> result = await execute_field_mapping(
        ...     context=context,
        ...     service_registry=service_registry,
        ...     raw_data=[{"cust_name": "Acme Inc", "cust_id": "123"}],
        ...     target_schema={"customer_name": "string", "customer_id": "string"}
        ... )
        >>> print(result["mapped_fields"])
        [
            {"source": "cust_name", "target": "customer_name", "confidence": 0.95},
            {"source": "cust_id", "target": "customer_id", "confidence": 0.90}
        ]

    Replaces:
        from app.services.crewai_flows.crews.field_mapping_crew import create_field_mapping_crew
        crew = create_field_mapping_crew(crewai_service, raw_data)
        result = crew.kickoff()
    """
    logger.info(
        f"Executing field mapping for {len(raw_data)} records "
        f"(client_account_id={context.client_account_id}, "
        f"engagement_id={context.engagement_id})"
    )

    # Get persistent agent
    agent = await get_persistent_field_mapper(context, service_registry)

    # Prepare input data
    input_data = {
        "raw_data": raw_data,
        "target_schema": target_schema,
        "confidence_threshold": confidence_threshold,
        **kwargs,
    }

    # Execute field mapping
    try:
        result = await agent.process(input_data)
        logger.info(
            f"✅ Field mapping completed: "
            f"{len(result.get('mapped_fields', []))} fields mapped, "
            f"{len(result.get('unmapped_fields', []))} unmapped"
        )
        return result
    except Exception as e:
        logger.error(f"❌ Field mapping failed: {e}", exc_info=True)
        raise


# Backward compatibility alias
async def create_persistent_field_mapper(
    context: RequestContext,
    service_registry: ServiceRegistry,
) -> Any:
    """
    Backward compatibility alias for get_persistent_field_mapper().

    Deprecated: Use get_persistent_field_mapper() instead.

    This function exists to maintain compatibility with code that uses
    the old naming convention (create_* instead of get_*).
    """
    logger.warning(
        "create_persistent_field_mapper() is deprecated. "
        "Use get_persistent_field_mapper() instead."
    )
    return await get_persistent_field_mapper(context, service_registry)
