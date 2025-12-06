"""
Tenant Scoped Agent Pool - Tool Management Module

This module handles tool management, configuration, and setup for agents
in the tenant scoped agent pool system.

Refactored per Issue #1060 to use declarative configuration pattern.
All agent-tool mappings are now centralized in agent_tool_config.py.
"""

import importlib
import inspect
import logging
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from app.services.persistent_agents.agent_tool_config import (
    COMMON_TOOL_CATEGORIES,
    get_agent_tool_config,
    get_tool_factory,
)

if TYPE_CHECKING:
    from app.services.service_registry import ServiceRegistry

logger = logging.getLogger(__name__)


class AgentToolManager:
    """Manages tools for agents in the tenant scoped agent pool."""

    @classmethod
    def extract_context_info(
        cls, context_info: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str], Optional["ServiceRegistry"]]:
        """
        Extract consistent context info from various input formats.

        Args:
            context_info: Dictionary containing context information

        Returns:
            Tuple of (client_account_id, engagement_id, service_registry)
        """
        client_account_id = context_info.get("client_account_id") or context_info.get(
            "client_id"
        )
        engagement_id = context_info.get("engagement_id")
        service_registry = context_info.get("service_registry")
        return client_account_id, engagement_id, service_registry

    @classmethod
    def add_tools_with_registry(
        cls,
        context_info: Dict[str, Any],
        tools: List,
        service_registry: Optional["ServiceRegistry"] = None,
    ) -> int:
        """Add tools using service registry if available."""
        if not service_registry:
            return 0

        tools_added = 0
        try:
            if hasattr(service_registry, "get_agent_tools"):
                registry_tools = service_registry.get_agent_tools(context_info)
                if registry_tools:
                    tools.extend(registry_tools)
                    tools_added += len(registry_tools)
                    logger.debug(f"Added {len(registry_tools)} registry tools")
            else:
                logger.debug(
                    "ServiceRegistry does not have get_agent_tools method - skipping"
                )
        except Exception as e:
            logger.warning(f"Failed to add registry tools: {e}")

        return tools_added

    @classmethod
    def _load_tool_from_factory(
        cls, tool_name: str, context_info: Dict[str, Any], tools: List
    ) -> int:
        """
        Load a tool using its factory configuration.

        Args:
            tool_name: Name of the tool to load
            context_info: Context information for tool initialization
            tools: List to append tools to

        Returns:
            Number of tools added
        """
        factory_config = get_tool_factory(tool_name)
        if not factory_config:
            logger.warning(f"No factory configuration found for tool '{tool_name}'")
            return 0

        try:
            module = importlib.import_module(factory_config.module_path)
            factory = getattr(module, factory_config.factory_name)

            if factory_config.is_class:
                # Instantiate class directly
                tool_instance = factory(context_info=context_info)
                tools.append(tool_instance)
                logger.debug(f"Added {tool_name} tool instance")
                return 1
            else:
                # Call factory function
                return cls._safe_extend_tools(tools, factory, tool_name, context_info)

        except ImportError as e:
            logger.error(f"Failed to import module for {tool_name}: {e}")
        except AttributeError as e:
            logger.error(f"Factory not found for {tool_name}: {e}")
        except Exception as e:
            logger.error(f"Failed to load {tool_name} tools: {e}", exc_info=True)

        return 0

    @classmethod
    def add_agent_specific_tools(
        cls, agent_type: str, context_info: Dict[str, Any], tools: List
    ) -> int:
        """Add tools specific to the agent type using declarative configuration."""
        tools_added = 0

        try:
            # Per ADR-037 #1114: Check if agent config has tools disabled
            from app.services.persistent_agents.agent_pool_constants import (
                get_agent_config,
            )

            config = get_agent_config(agent_type)
            if config.get("tools") is not None and len(config.get("tools", [])) == 0:
                logger.info(
                    f"Skipping tool loading for {agent_type} - "
                    f"agent config has empty tools list per ADR-037 #1114"
                )
                return 0

            # Get tool configuration for this agent type
            tool_config = get_agent_tool_config(agent_type)
            if not tool_config:
                logger.debug(
                    f"No tool configuration found for agent type: {agent_type}"
                )
                return 0

            # Load each specific tool using factory configuration
            for tool_name in tool_config.specific_tools:
                tools_added += cls._load_tool_from_factory(
                    tool_name, context_info, tools
                )

            logger.debug(f"Added {tools_added} {agent_type}-specific tools")

        except Exception as e:
            logger.warning(f"Failed to add {agent_type} tools: {e}")

        return tools_added

    @classmethod
    def _add_common_category_tools(
        cls, agent_type: str, context_info: Dict[str, Any], tools: List
    ) -> int:
        """Add common tool category tools based on agent configuration."""
        tools_added = 0

        try:
            from app.services.persistent_agents.tool_adders import ToolAdders
            from app.services.persistent_agents.agent_pool_constants import (
                get_agent_config,
            )

            tool_config = get_agent_tool_config(agent_type)
            if not tool_config:
                return 0

            # Check if tools are disabled per ADR-037
            agent_config = get_agent_config(agent_type)
            has_tools_disabled = (
                agent_config.get("tools") is not None
                and len(agent_config.get("tools", [])) == 0
            )

            for category in tool_config.common_categories:
                if has_tools_disabled:
                    logger.info(
                        f"Skipping {category} tools for {agent_type} - "
                        f"agent config has empty tools list per ADR-037 #1114"
                    )
                    continue

                method_name = COMMON_TOOL_CATEGORIES.get(category)
                if method_name and hasattr(ToolAdders, method_name):
                    adder_method = getattr(ToolAdders, method_name)
                    result = adder_method(context_info, tools)
                    if isinstance(result, int):
                        tools_added += result

        except Exception as e:
            logger.warning(f"Failed to add common category tools for {agent_type}: {e}")

        return tools_added

    @classmethod
    def _validate_tools(cls, tools: List, context: str = "") -> List[Any]:
        """Validate that all tools are BaseTool instances."""
        try:
            from crewai.tools import BaseTool
        except ImportError:
            logger.warning("CrewAI BaseTool not available - skipping validation")
            return tools

        valid_tools = []
        for tool in tools:
            if isinstance(tool, BaseTool):
                valid_tools.append(tool)
            else:
                logger.error(
                    f"INVALID_TOOL_TYPE in {context}: {type(tool).__name__} "
                    f"is not a BaseTool instance.",
                    extra={
                        "tool_type": type(tool).__name__,
                        "tool_name": getattr(tool, "name", "unknown"),
                        "context": context,
                    },
                )

        if len(valid_tools) < len(tools):
            logger.warning(
                f"Filtered {len(tools) - len(valid_tools)} invalid tools in {context}"
            )

        return valid_tools

    @classmethod
    def _safe_extend_tools(
        cls,
        tools: List,
        getter,
        tool_name: str = "tools",
        context_info: Dict[str, Any] = None,
    ) -> int:
        """Safely extend tools list with error handling."""
        if not getter:
            logger.warning(f"Skipping {tool_name} - getter is None or False")
            return 0

        try:
            sig = inspect.signature(getter)
            params = sig.parameters

            logger.debug(f"Tool {tool_name} - signature params: {list(params.keys())}")

            # CC: Check if function requires registry parameter
            if "registry" in params:
                service_registry = (
                    context_info.get("service_registry") if context_info else None
                )
                if service_registry is None:
                    logger.warning(
                        f"Skipping {tool_name} - ServiceRegistry not available."
                    )
                    return 0

                if "context_info" in params:
                    new_tools = getter(context_info, registry=service_registry)
                else:
                    new_tools = getter(registry=service_registry)
            elif "context_info" in params and context_info is not None:
                new_tools = getter(context_info)
            elif "field_mapper" in params:
                new_tools = getter(field_mapper=None)
            else:
                new_tools = getter()

            if new_tools:
                tools.extend(new_tools)
                logger.info(f"Successfully added {len(new_tools)} {tool_name}")
                return len(new_tools)
            else:
                logger.warning(f"Tool {tool_name} getter returned None or empty list")

        except Exception as e:
            logger.error(f"Failed to add {tool_name}: {e}", exc_info=True)

        return 0

    @classmethod
    def get_agent_tools(
        cls, agent_type: str, context_info: Dict[str, Any]
    ) -> List[Any]:
        """Get comprehensive toolset for agent type using declarative configuration."""
        tools = []

        try:
            # Extract context information
            client_account_id, engagement_id, service_registry = (
                cls.extract_context_info(context_info)
            )

            logger.debug(
                f"Getting tools for {agent_type}. "
                f"ServiceRegistry available: {service_registry is not None}"
            )

            # Add registry-based tools
            cls.add_tools_with_registry(context_info, tools, service_registry)

            # Add agent-specific tools from declarative config
            cls.add_agent_specific_tools(agent_type, context_info, tools)

            # Add common category tools from declarative config
            cls._add_common_category_tools(agent_type, context_info, tools)

            logger.info(f"Configured {len(tools)} tools for {agent_type} agent")

            # Validate all tools are BaseTool instances
            tools = cls._validate_tools(tools, context=f"{agent_type} agent")

            logger.info(
                f"Validated {len(tools)} tools for {agent_type} agent after filtering"
            )

        except Exception as e:
            logger.error(f"Error configuring tools for {agent_type}: {e}")
            tools = []

        return tools
