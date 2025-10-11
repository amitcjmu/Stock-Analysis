"""
Persistent Data Import Validation Agent Wrapper (ADR-015, ADR-024)

This module provides a persistent agent wrapper for data import validation operations.
Replaces: app.services.crewai_flows.crews.data_import_validation_crew

Architecture:
- Uses TenantScopedAgentPool for agent lifecycle management
- Single agent instance per (tenant, agent_type) - singleton pattern
- Memory managed by TenantMemoryManager (memory=False for crews per ADR-024)

Migration Context:
- Part of Workstream B, Phase B1: Create Persistent Agent Wrappers
- Task B1.4: Data Import Validation Wrapper
- Created: 2025-10-11
"""

from typing import Any, Dict, List, Optional
import logging

from app.core.context import RequestContext
from app.services.service_registry import ServiceRegistry
from app.services.persistent_agents import TenantScopedAgentPool

logger = logging.getLogger(__name__)


async def get_persistent_data_import_validator(
    context: RequestContext,
    service_registry: ServiceRegistry,
) -> Any:
    """
    Get or create persistent data import validation agent.

    This function replaces direct crew instantiation with persistent agent pattern.

    Args:
        context: Request context with client_account_id and engagement_id
        service_registry: Service registry for agent dependencies

    Returns:
        Persistent agent configured for data import validation

    Example:
        >>> agent = await get_persistent_data_import_validator(context, service_registry)
        >>> result = await agent.process(import_data)

    Replaces:
        from app.services.crewai_flows.crews.data_import_validation_crew import create_validation_crew
        crew = create_validation_crew(crewai_service, import_data)

    Architecture:
        - Singleton per (tenant, agent_type)
        - Lazy initialization
        - Memory=False (uses TenantMemoryManager per ADR-024)
    """
    logger.info(
        f"Getting persistent data import validation agent for "
        f"client_account_id={context.client_account_id}, "
        f"engagement_id={context.engagement_id}"
    )

    agent = await TenantScopedAgentPool.get_agent(
        context=context,
        agent_type="data_import_validation",
        service_registry=service_registry,
    )

    logger.debug(
        f"✅ Persistent data import validation agent retrieved: {type(agent).__name__}"
    )
    return agent


async def execute_data_import_validation(
    context: RequestContext,
    service_registry: ServiceRegistry,
    import_data: List[Dict[str, Any]],
    validation_rules: Optional[Dict[str, Any]] = None,
    strict_mode: bool = False,
    auto_fix_enabled: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """
    Execute data import validation using persistent agent.

    High-level convenience function that gets the agent and processes data
    in a single call.

    Args:
        context: Request context
        service_registry: Service registry
        import_data: Data to validate for import
        validation_rules: Optional custom validation rules
        strict_mode: Whether to fail on any validation error (vs. warnings)
        auto_fix_enabled: Whether to attempt automatic fixes for common issues
        **kwargs: Additional parameters passed to agent.process()

    Returns:
        Dict containing:
            - is_valid: Overall validation status
            - validation_errors: List of validation errors found
            - validation_warnings: List of validation warnings
            - fixed_records: Records that were automatically fixed (if auto_fix_enabled)
            - data_quality_score: Overall data quality score (0-100)
            - recommendations: Recommendations for data cleanup
            - metadata: Processing metadata

    Example:
        >>> result = await execute_data_import_validation(
        ...     context=context,
        ...     service_registry=service_registry,
        ...     import_data=[
        ...         {"app_name": "CustomerPortal", "owner": ""},
        ...         {"app_name": "OrderService", "owner": "IT Team"}
        ...     ],
        ...     validation_rules={
        ...         "required_fields": ["app_name", "owner"],
        ...         "field_formats": {"app_name": "^[A-Za-z][A-Za-z0-9_]*$"}
        ...     },
        ...     strict_mode=False,
        ...     auto_fix_enabled=True
        ... )
        >>> print(result["validation_errors"])
        [
            {
                "record_index": 0,
                "field": "owner",
                "error": "required_field_missing",
                "message": "Owner field is required but empty"
            }
        ]

    Replaces:
        from app.services.crewai_flows.crews.data_import_validation_crew import create_validation_crew
        crew = create_validation_crew(crewai_service, import_data)
        result = crew.kickoff()
    """
    logger.info(
        f"Executing data import validation for {len(import_data)} records "
        f"(strict={strict_mode}, auto_fix={auto_fix_enabled}, "
        f"client_account_id={context.client_account_id})"
    )

    # Get persistent agent
    agent = await get_persistent_data_import_validator(context, service_registry)

    # Prepare input data
    input_data = {
        "import_data": import_data,
        "validation_rules": validation_rules,
        "strict_mode": strict_mode,
        "auto_fix_enabled": auto_fix_enabled,
        **kwargs,
    }

    # Execute data import validation
    try:
        result = await agent.process(input_data)
        logger.info(
            f"✅ Data import validation completed: "
            f"valid={result.get('is_valid', False)}, "
            f"errors={len(result.get('validation_errors', []))}, "
            f"warnings={len(result.get('validation_warnings', []))}, "
            f"quality_score={result.get('data_quality_score', 'N/A')}"
        )
        return result
    except Exception as e:
        logger.error(f"❌ Data import validation failed: {e}", exc_info=True)
        raise


async def validate_application_import(
    context: RequestContext,
    service_registry: ServiceRegistry,
    applications: List[Dict[str, Any]],
    **kwargs,
) -> Dict[str, Any]:
    """
    Convenience function for validating application data imports.

    Executes validation specifically for application inventory data,
    with predefined rules for application fields.

    Args:
        context: Request context
        service_registry: Service registry
        applications: List of applications to validate
        **kwargs: Additional parameters

    Returns:
        Validation results for application data

    Example:
        >>> result = await validate_application_import(
        ...     context=context,
        ...     service_registry=service_registry,
        ...     applications=[
        ...         {"name": "App1", "type": "web", "owner": "Team A"},
        ...         {"name": "App2", "type": "api", "owner": "Team B"}
        ...     ]
        ... )
    """
    # Define standard application validation rules
    application_rules = {
        "required_fields": ["name", "type", "owner"],
        "field_formats": {
            "name": "^[A-Za-z][A-Za-z0-9_\\-]*$",
            "type": "^(web|api|service|database|batch)$",
        },
        "unique_fields": ["name"],
    }

    return await execute_data_import_validation(
        context=context,
        service_registry=service_registry,
        import_data=applications,
        validation_rules=application_rules,
        **kwargs,
    )


async def validate_server_import(
    context: RequestContext,
    service_registry: ServiceRegistry,
    servers: List[Dict[str, Any]],
    **kwargs,
) -> Dict[str, Any]:
    """
    Convenience function for validating server data imports.

    Executes validation specifically for server inventory data,
    with predefined rules for server fields.

    Args:
        context: Request context
        service_registry: Service registry
        servers: List of servers to validate
        **kwargs: Additional parameters

    Returns:
        Validation results for server data

    Example:
        >>> result = await validate_server_import(
        ...     context=context,
        ...     service_registry=service_registry,
        ...     servers=[
        ...         {"hostname": "web-01", "ip_address": "192.168.1.10", "os": "Linux"},
        ...         {"hostname": "db-01", "ip_address": "192.168.1.20", "os": "Linux"}
        ...     ]
        ... )
    """
    # Define standard server validation rules
    server_rules = {
        "required_fields": ["hostname", "ip_address", "os"],
        "field_formats": {
            "hostname": "^[a-z0-9\\-]+$",
            "ip_address": "^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$",
        },
        "unique_fields": ["hostname", "ip_address"],
    }

    return await execute_data_import_validation(
        context=context,
        service_registry=service_registry,
        import_data=servers,
        validation_rules=server_rules,
        **kwargs,
    )


# Backward compatibility alias
async def create_persistent_data_import_validator(
    context: RequestContext,
    service_registry: ServiceRegistry,
) -> Any:
    """
    Backward compatibility alias for get_persistent_data_import_validator().

    Deprecated: Use get_persistent_data_import_validator() instead.
    """
    logger.warning(
        "create_persistent_data_import_validator() is deprecated. "
        "Use get_persistent_data_import_validator() instead."
    )
    return await get_persistent_data_import_validator(context, service_registry)
