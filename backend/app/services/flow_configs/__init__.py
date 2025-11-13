"""
Flow Configurations Module
MFO-056: Register all flows with registry

This module provides centralized access to all flow configurations and
handles registration of all flow types with the registry.
"""

from typing import Any, Dict, List

# Import registry manager
from .registry_manager import (
    FlowConfigurationManager,
    flow_configuration_manager,
)

# Import flow configuration getters
from .assessment_flow_config import get_assessment_flow_config
from .collection_flow_config import get_collection_flow_config
from .decommission_flow_config import get_decommission_flow_config
from .discovery_flow_config import get_discovery_flow_config
from .execution_flow_config import get_execution_flow_config
from .finops_flow_config import get_finops_flow_config
from .modernize_flow_config import get_modernize_flow_config
from .observability_flow_config import get_observability_flow_config
from .planning_flow_config import get_planning_flow_config


def initialize_all_flows() -> Dict[str, Any]:
    """Initialize all flow configurations"""
    return flow_configuration_manager.initialize_all_flows()


def verify_flow_configurations() -> Dict[str, Any]:
    """Verify all flow configurations"""
    return flow_configuration_manager.verify_all_flows()


def get_flow_summary() -> List[Dict[str, Any]]:
    """Get summary of all registered flows"""
    return flow_configuration_manager.get_flow_summary()


# Export key items
__all__ = [
    "FlowConfigurationManager",
    "flow_configuration_manager",
    "initialize_all_flows",
    "verify_flow_configurations",
    "get_flow_summary",
    "get_discovery_flow_config",
    "get_assessment_flow_config",
    "get_collection_flow_config",
    "get_planning_flow_config",
    "get_execution_flow_config",
    "get_modernize_flow_config",
    "get_finops_flow_config",
    "get_observability_flow_config",
    "get_decommission_flow_config",
]
