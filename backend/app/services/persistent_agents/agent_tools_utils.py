"""
Agent Tools Utilities

This module contains utility functions for managing agent tools.
Extracted from tenant_scoped_agent_pool.py to maintain file length limits.
"""

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.service_registry import ServiceRegistry

# Move all tool imports to module level to avoid per-call dynamic imports
try:
    from app.services.crewai_flows.tools.asset_creation_tool import (
        create_asset_creation_tools,
    )
    from app.services.crewai_flows.tools.task_completion_tools import (
        create_task_completion_tools,
    )
    from app.services.crewai_flows.tools.data_validation_tool import (
        create_data_validation_tools,
    )
    from app.services.crewai_flows.tools.critical_attributes_tool import (
        create_critical_attributes_tools,
    )
    from app.services.crewai_flows.tools.dependency_analysis_tool import (
        create_dependency_analysis_tools,
    )
    from app.services.crewai_flows.tools.mapping_confidence_tool import (
        MappingConfidenceTool,
    )
    from app.services.tools.asset_intelligence_tools import (
        get_asset_intelligence_tools,
    )

    TOOLS_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Some tools not available: {e}")
    TOOLS_AVAILABLE = False
    # Define placeholders for missing imports
    create_asset_creation_tools = None
    create_task_completion_tools = None
    create_data_validation_tools = None
    create_critical_attributes_tools = None
    create_dependency_analysis_tools = None
    MappingConfidenceTool = None
    get_asset_intelligence_tools = None


logger = logging.getLogger(__name__)


def add_tools_with_registry(
    service_registry: Optional["ServiceRegistry"],
    agent_type: str,
    context_info: Dict[str, Any],
    tools: List,
) -> int:
    """Add tools to agent using service registry if available.

    Args:
        service_registry: Service registry instance
        agent_type: Type of agent
        context_info: Context information
        tools: List to add tools to

    Returns:
        Number of tools added
    """
    if not service_registry:
        return 0

    tools_added = 0

    # Try to get specialized tools from registry
    try:
        if hasattr(service_registry, "get_agent_tools"):
            registry_tools = service_registry.get_agent_tools(
                agent_type=agent_type, context=context_info
            )
            if registry_tools:
                tools.extend(registry_tools)
                tools_added += len(registry_tools)
                logger.debug(
                    f"Added {len(registry_tools)} tools from service registry for {agent_type}"
                )
    except Exception as e:
        logger.warning(f"Failed to get tools from service registry: {e}")

    return tools_added


def add_agent_specific_tools(
    agent_type: str, context_info: Dict[str, Any], tools: List
) -> int:
    """Add agent type-specific tools.

    Args:
        agent_type: Type of agent
        context_info: Context information
        tools: List to add tools to

    Returns:
        Number of tools added
    """
    tools_added = 0

    # Add specific tools based on agent type
    if agent_type == "discovery_specialist":
        tools_added += add_discovery_tools(context_info, tools)
    elif agent_type == "gap_analysis_specialist":
        tools_added += add_gap_analysis_tools(context_info, tools)
    elif agent_type == "business_impact_assessor":
        tools_added += add_business_analysis_tools(context_info, tools)
    elif agent_type == "quality_validator":
        tools_added += add_quality_tools(context_info, tools)
    elif agent_type == "dependency_analyst":
        tools_added += add_dependency_tools(context_info, tools)

    return tools_added


def add_discovery_tools(context_info: Dict[str, Any], tools: List) -> int:
    """Add discovery-specific tools.

    Args:
        context_info: Context information
        tools: List to add tools to

    Returns:
        Number of tools added
    """
    tools_added = 0

    # Asset creation tools
    tools_added += safe_extend_tools(
        tools, create_asset_creation_tools, "asset_creation_tools"
    )

    # Data validation tools
    tools_added += safe_extend_tools(
        tools, create_data_validation_tools, "data_validation_tools"
    )

    # Critical attributes tools
    tools_added += safe_extend_tools(
        tools, create_critical_attributes_tools, "critical_attributes_tools"
    )

    return tools_added


def add_gap_analysis_tools(context_info: Dict[str, Any], tools: List) -> int:
    """Add gap analysis-specific tools.

    Args:
        context_info: Context information
        tools: List to add tools to

    Returns:
        Number of tools added
    """
    tools_added = 0

    # Data validation tools
    tools_added += safe_extend_tools(
        tools, create_data_validation_tools, "data_validation_tools"
    )

    # Critical attributes tools
    tools_added += safe_extend_tools(
        tools, create_critical_attributes_tools, "critical_attributes_tools"
    )

    return tools_added


def add_business_analysis_tools(context_info: Dict[str, Any], tools: List) -> int:
    """Add business analysis-specific tools.

    Args:
        context_info: Context information
        tools: List to add tools to

    Returns:
        Number of tools added
    """
    tools_added = 0

    # Task completion tools
    tools_added += safe_extend_tools(
        tools, create_task_completion_tools, "task_completion_tools"
    )

    # Mapping confidence tools
    if MappingConfidenceTool:
        try:
            confidence_tool = MappingConfidenceTool()
            tools.append(confidence_tool)
            tools_added += 1
        except Exception as e:
            logger.warning(f"Failed to add mapping confidence tool: {e}")

    return tools_added


def add_quality_tools(context_info: Dict[str, Any], tools: List) -> int:
    """Add quality validation-specific tools.

    Args:
        context_info: Context information
        tools: List to add tools to

    Returns:
        Number of tools added
    """
    tools_added = 0

    # Data validation tools
    tools_added += safe_extend_tools(
        tools, create_data_validation_tools, "data_validation_tools"
    )

    return tools_added


def add_dependency_tools(context_info: Dict[str, Any], tools: List) -> int:
    """Add dependency analysis-specific tools.

    Args:
        context_info: Context information
        tools: List to add tools to

    Returns:
        Number of tools added
    """
    tools_added = 0

    # Dependency analysis tools
    tools_added += safe_extend_tools(
        tools, create_dependency_analysis_tools, "dependency_analysis_tools"
    )

    # Asset intelligence tools
    tools_added += safe_extend_tools(
        tools, get_asset_intelligence_tools, "asset_intelligence_tools"
    )

    return tools_added


def safe_extend_tools(tools: List, getter, tool_name: str = "tools") -> int:
    """Safely extend tools list with tools from a getter function.

    Args:
        tools: List to extend
        getter: Function to get tools
        tool_name: Name of tools for logging

    Returns:
        Number of tools added
    """
    if not getter or not TOOLS_AVAILABLE:
        return 0

    try:
        new_tools = getter()
        if new_tools:
            if isinstance(new_tools, list):
                tools.extend(new_tools)
                added_count = len(new_tools)
            else:
                tools.append(new_tools)
                added_count = 1

            logger.debug(f"Added {added_count} {tool_name}")
            return added_count
    except Exception as e:
        logger.warning(f"Failed to add {tool_name}: {e}")

    return 0


def get_agent_tools(
    agent_type: str,
    client_id: str,
    engagement_id: str,
    service_registry: Optional["ServiceRegistry"] = None,
) -> List:
    """Get tools for a specific agent type and context.

    Args:
        agent_type: Type of agent
        client_id: Client account ID
        engagement_id: Engagement ID
        service_registry: Optional service registry

    Returns:
        List of tools for the agent
    """
    tools = []

    # Extract context information for tools
    context_info = {
        "client_id": client_id,
        "engagement_id": engagement_id,
        "agent_type": agent_type,
    }

    # Add tools using service registry if available
    tools_added = add_tools_with_registry(
        service_registry, agent_type, context_info, tools
    )

    # Add agent-specific tools
    agent_tools_added = add_agent_specific_tools(agent_type, context_info, tools)

    total_tools = tools_added + agent_tools_added

    if total_tools > 0:
        logger.info(f"✅ {agent_type} agent equipped with {total_tools} tools")
    else:
        logger.warning(f"⚠️ {agent_type} agent has no tools available")

    return tools
