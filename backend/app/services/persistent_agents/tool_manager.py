"""
Tenant Scoped Agent Pool - Tool Management Module

This module handles tool management, configuration, and setup for agents
in the tenant scoped agent pool system.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.service_registry import ServiceRegistry

# Move all tool imports to module level to avoid per-call dynamic imports
# This improves performance and avoids repeated import overhead
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
        # Extract client_account_id
        client_account_id = context_info.get("client_account_id") or context_info.get(
            "client_id"
        )

        # Extract engagement_id
        engagement_id = context_info.get("engagement_id")

        # Extract service_registry if available
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
            # Add registry-based tools if available
            registry_tools = service_registry.get_agent_tools(context_info)
            if registry_tools:
                tools.extend(registry_tools)
                tools_added += len(registry_tools)
                logger.debug(f"Added {len(registry_tools)} registry tools")
        except Exception as e:
            logger.warning(f"Failed to add registry tools: {e}")

        return tools_added

    @classmethod
    def add_agent_specific_tools(
        cls, agent_type: str, context_info: Dict[str, Any], tools: List
    ) -> int:
        """Add tools specific to the agent type."""
        if not TOOLS_AVAILABLE:
            return 0

        tools_added = 0

        try:
            if agent_type == "discovery":
                # Discovery-specific tools
                tools_added += cls._safe_extend_tools(
                    tools, create_asset_creation_tools, "asset creation", context_info
                )
                tools_added += cls._safe_extend_tools(
                    tools, create_data_validation_tools, "data validation", context_info
                )

            elif agent_type == "field_mapper":
                # Field mapping tools
                if MappingConfidenceTool:
                    tools.append(MappingConfidenceTool(context_info=context_info))
                    tools_added += 1

                tools_added += cls._safe_extend_tools(
                    tools,
                    create_critical_attributes_tools,
                    "critical attributes",
                    context_info,
                )

            elif agent_type == "questionnaire_generator":
                # Questionnaire tools
                tools_added += cls._safe_extend_tools(
                    tools, create_task_completion_tools, "task completion", context_info
                )

            elif agent_type == "six_r_analyzer":
                # 6R analysis tools
                tools_added += cls._safe_extend_tools(
                    tools,
                    create_dependency_analysis_tools,
                    "dependency analysis",
                    context_info,
                )
                tools_added += cls._safe_extend_tools(
                    tools,
                    get_asset_intelligence_tools,
                    "asset intelligence",
                    context_info,
                )

            elif agent_type == "asset_inventory_agent":
                # Asset inventory-specific tools for database asset creation
                tools_added += cls._safe_extend_tools(
                    tools, create_asset_creation_tools, "asset creation", context_info
                )
                tools_added += cls._safe_extend_tools(
                    tools, create_data_validation_tools, "data validation", context_info
                )

            logger.debug(f"Added {tools_added} {agent_type}-specific tools")
        except Exception as e:
            logger.warning(f"Failed to add {agent_type} tools: {e}")

        return tools_added

    @classmethod
    def add_legacy_tools(cls, context_info: Dict[str, Any], tools: List) -> int:
        """Add legacy tools for backward compatibility."""
        if not TOOLS_AVAILABLE:
            return 0

        tools_added = 0
        try:
            # Add common legacy tools
            tools_added += cls._safe_extend_tools(
                tools,
                create_asset_creation_tools,
                "legacy asset creation",
                context_info,
            )
            tools_added += cls._safe_extend_tools(
                tools,
                create_task_completion_tools,
                "legacy task completion",
                context_info,
            )

            logger.debug(f"Added {tools_added} legacy tools")
        except Exception as e:
            logger.warning(f"Failed to add legacy tools: {e}")

        return tools_added

    @classmethod
    def add_data_analysis_tools(cls, context_info: Dict[str, Any], tools: List) -> int:
        """Add data analysis and validation tools."""
        if not TOOLS_AVAILABLE:
            return 0

        tools_added = 0
        try:
            tools_added += cls._safe_extend_tools(
                tools, create_data_validation_tools, "data validation", context_info
            )
            tools_added += cls._safe_extend_tools(
                tools,
                create_critical_attributes_tools,
                "critical attributes",
                context_info,
            )

            logger.debug(f"Added {tools_added} data analysis tools")
        except Exception as e:
            logger.warning(f"Failed to add data analysis tools: {e}")

        return tools_added

    @classmethod
    def add_quality_tools(cls, context_info: Dict[str, Any], tools: List) -> None:
        """Add quality assurance and validation tools."""
        if not TOOLS_AVAILABLE:
            return

        try:
            # Add quality-focused tools
            cls._safe_extend_tools(
                tools, create_data_validation_tools, "quality validation", context_info
            )
            logger.debug("Added quality tools")
        except Exception as e:
            logger.warning(f"Failed to add quality tools: {e}")

    @classmethod
    def add_business_analysis_tools(
        cls, context_info: Dict[str, Any], tools: List
    ) -> int:
        """Add business analysis and decision support tools."""
        if not TOOLS_AVAILABLE:
            return 0

        tools_added = 0
        try:
            tools_added += cls._safe_extend_tools(
                tools,
                create_dependency_analysis_tools,
                "business dependency analysis",
                context_info,
            )
            tools_added += cls._safe_extend_tools(
                tools,
                get_asset_intelligence_tools,
                "business asset intelligence",
                context_info,
            )

            logger.debug(f"Added {tools_added} business analysis tools")
        except Exception as e:
            logger.warning(f"Failed to add business analysis tools: {e}")

        return tools_added

    @classmethod
    def add_field_mapper_tools(cls, context_info: Dict[str, Any], tools: List) -> None:
        """Add field mapping specific tools."""
        if not TOOLS_AVAILABLE:
            return

        try:
            if MappingConfidenceTool:
                tools.append(MappingConfidenceTool(context_info=context_info))
                logger.debug("Added field mapper tools")
        except Exception as e:
            logger.warning(f"Failed to add field mapper tools: {e}")

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
            return 0

        try:
            # Check if getter function requires context_info parameter
            import inspect

            sig = inspect.signature(getter)
            params = sig.parameters

            # CC: Check if function requires registry parameter (for new tool pattern)
            if "registry" in params:
                # Extract service_registry from context_info if available
                service_registry = (
                    context_info.get("service_registry") if context_info else None
                )
                if "context_info" in params:
                    new_tools = getter(context_info, registry=service_registry)
                else:
                    new_tools = getter(registry=service_registry)
            elif "context_info" in params and context_info is not None:
                new_tools = getter(context_info)
            else:
                new_tools = getter()

            if new_tools:
                tools.extend(new_tools)
                logger.debug(f"Added {len(new_tools)} {tool_name}")
                return len(new_tools)
        except Exception as e:
            logger.warning(f"Failed to add {tool_name}: {e}")

        return 0

    @classmethod
    def get_agent_tools(
        cls, agent_type: str, context_info: Dict[str, Any]
    ) -> List[Any]:
        """Get comprehensive toolset for agent type."""
        tools = []

        try:
            # Extract context information
            client_account_id, engagement_id, service_registry = (
                cls.extract_context_info(context_info)
            )

            # Add registry-based tools
            cls.add_tools_with_registry(context_info, tools, service_registry)

            # Add agent-specific tools
            cls.add_agent_specific_tools(agent_type, context_info, tools)

            # Add common tools based on agent type
            if agent_type in [
                "discovery",
                "field_mapper",
                "data_cleansing",
                "asset_inventory_agent",
            ]:
                cls.add_data_analysis_tools(context_info, tools)

            if agent_type in ["questionnaire_generator", "six_r_analyzer"]:
                cls.add_business_analysis_tools(context_info, tools)

            # Add quality tools for all agents
            cls.add_quality_tools(context_info, tools)

            # Add legacy tools for backward compatibility
            cls.add_legacy_tools(context_info, tools)

            logger.info(f"Configured {len(tools)} tools for {agent_type} agent")

        except Exception as e:
            logger.error(f"Error configuring tools for {agent_type}: {e}")
            # Return empty list rather than None to prevent errors
            tools = []

        return tools
