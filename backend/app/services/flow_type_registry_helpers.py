"""
Flow Type Registry Helper Functions
Provides module-level convenience functions for accessing the registry
"""

from typing import List
from app.services.flow_type_registry import (
    flow_type_registry,
    FlowTypeConfig,
)


def get_flow_config(flow_type: str) -> FlowTypeConfig:
    """
    Get configuration for a flow type

    Convenience wrapper around flow_type_registry.get_flow_config()

    Args:
        flow_type: Name of the flow type

    Returns:
        Flow type configuration

    Raises:
        ValueError: If flow type not found
    """
    return flow_type_registry.get_flow_config(flow_type)


def get_all_flow_configs() -> List[FlowTypeConfig]:
    """
    Get all registered flow configurations

    Returns:
        List of all flow type configurations
    """
    configs_dict = flow_type_registry.get_all_configurations()
    return list(configs_dict.values())


def register_flow_config(config: FlowTypeConfig) -> None:
    """
    Register a new flow type configuration

    Convenience wrapper around flow_type_registry.register()

    Args:
        config: Flow type configuration to register

    Raises:
        ValueError: If configuration is invalid or name already exists
    """
    flow_type_registry.register(config)


def is_flow_registered(flow_type: str) -> bool:
    """
    Check if a flow type is registered

    Args:
        flow_type: Name of the flow type

    Returns:
        True if registered, False otherwise
    """
    return flow_type_registry.is_registered(flow_type)


def initialize_default_flow_configs() -> None:
    """
    Initialize default flow configurations

    Called at application startup to register all flow types.
    MUST be called before any flow operations.
    """
    # Import here to avoid circular dependencies
    from app.services.flow_configs.discovery_flow_config import (
        get_discovery_flow_config,
    )
    from app.services.flow_configs.collection_flow_config import (
        get_collection_flow_config,
    )
    from app.services.flow_configs.assessment_flow_config import (
        get_assessment_flow_config,
    )

    # Register each flow type
    if not is_flow_registered("discovery"):
        register_flow_config(get_discovery_flow_config())

    if not is_flow_registered("collection"):
        register_flow_config(get_collection_flow_config())

    if not is_flow_registered("assessment"):
        register_flow_config(get_assessment_flow_config())

    # Add other flows as they are migrated
    # ...

    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        f"✅ Initialized {len(flow_type_registry.list_flow_types())} flow type(s)"
    )
