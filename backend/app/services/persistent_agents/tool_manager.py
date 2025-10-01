"""
Tenant Scoped Agent Pool - Tool Management Module

This module handles tool management, configuration, and setup for agents
in the tenant scoped agent pool system.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.service_registry import ServiceRegistry

# CC: Use lazy imports to avoid circular dependency with tenant_scoped_agent_pool
# Tools are imported inside functions when needed, not at module level
TOOLS_AVAILABLE = True  # Set to True since we'll handle import errors per-tool

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
            # Check if service_registry has get_agent_tools method
            if hasattr(service_registry, "get_agent_tools"):
                registry_tools = service_registry.get_agent_tools(context_info)
                if registry_tools:
                    tools.extend(registry_tools)
                    tools_added += len(registry_tools)
                    logger.debug(f"Added {len(registry_tools)} registry tools")
            else:
                logger.debug(
                    "ServiceRegistry does not have get_agent_tools method - skipping registry tools"
                )
        except Exception as e:
            logger.warning(f"Failed to add registry tools: {e}")

        return tools_added

    @classmethod
    def add_agent_specific_tools(
        cls, agent_type: str, context_info: Dict[str, Any], tools: List
    ) -> int:
        """Add tools specific to the agent type."""
        tools_added = 0

        try:
            if agent_type == "discovery":
                # Discovery-specific tools - lazy import
                from app.services.crewai_flows.tools.asset_creation_tool import (
                    create_asset_creation_tools,
                )
                from app.services.crewai_flows.tools.data_validation_tool import (
                    create_data_validation_tools,
                )

                tools_added += cls._safe_extend_tools(
                    tools, create_asset_creation_tools, "asset creation", context_info
                )
                tools_added += cls._safe_extend_tools(
                    tools, create_data_validation_tools, "data validation", context_info
                )

            elif agent_type == "field_mapper":
                # Field mapping tools - lazy import
                from app.services.crewai_flows.tools.mapping_confidence_tool import (
                    MappingConfidenceTool,
                )
                from app.services.crewai_flows.tools.critical_attributes_tool import (
                    create_critical_attributes_tools,
                )

                tools.append(MappingConfidenceTool(context_info=context_info))
                tools_added += 1

                tools_added += cls._safe_extend_tools(
                    tools,
                    create_critical_attributes_tools,
                    "critical attributes",
                    context_info,
                )

            elif agent_type == "questionnaire_generator":
                # Questionnaire generation tools - lazy import
                from app.services.ai_analysis.questionnaire_generator.tools import (
                    create_questionnaire_generation_tools,
                    create_gap_analysis_tools,
                )
                from app.services.tools.asset_intelligence_tools import (
                    get_asset_intelligence_tools,
                )

                tools_added += cls._safe_extend_tools(
                    tools,
                    create_questionnaire_generation_tools,
                    "questionnaire generation",
                    context_info,
                )
                tools_added += cls._safe_extend_tools(
                    tools, create_gap_analysis_tools, "gap analysis", context_info
                )
                tools_added += cls._safe_extend_tools(
                    tools,
                    get_asset_intelligence_tools,
                    "asset intelligence",
                    context_info,
                )

            elif agent_type == "business_value_analyst":
                # Business value analysis tools - lazy import
                from app.services.ai_analysis.questionnaire_generator.tools import (
                    create_questionnaire_generation_tools,
                    create_gap_analysis_tools,
                )
                from app.services.tools.asset_intelligence_tools import (
                    get_asset_intelligence_tools,
                )

                tools_added += cls._safe_extend_tools(
                    tools, create_gap_analysis_tools, "gap analysis", context_info
                )
                tools_added += cls._safe_extend_tools(
                    tools,
                    create_questionnaire_generation_tools,
                    "questionnaire generation",
                    context_info,
                )
                tools_added += cls._safe_extend_tools(
                    tools,
                    get_asset_intelligence_tools,
                    "asset intelligence",
                    context_info,
                )

            elif agent_type == "six_r_analyzer":
                # 6R analysis tools - lazy import
                from app.services.crewai_flows.tools.dependency_analysis_tool import (
                    create_dependency_analysis_tools,
                )
                from app.services.tools.asset_intelligence_tools import (
                    get_asset_intelligence_tools,
                )

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

            elif agent_type == "asset_inventory":
                # Asset inventory tools - lazy import
                from app.services.crewai_flows.tools.asset_creation_tool import (
                    create_asset_creation_tools,
                )
                from app.services.crewai_flows.tools.data_validation_tool import (
                    create_data_validation_tools,
                )

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
        tools_added = 0
        try:
            # Lazy import legacy tools
            from app.services.crewai_flows.tools.asset_creation_tool import (
                create_asset_creation_tools,
            )
            from app.services.crewai_flows.tools.task_completion_tools import (
                create_task_completion_tools,
            )

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
        tools_added = 0
        try:
            # Lazy import data analysis tools
            from app.services.crewai_flows.tools.data_validation_tool import (
                create_data_validation_tools,
            )
            from app.services.crewai_flows.tools.critical_attributes_tool import (
                create_critical_attributes_tools,
            )

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
        try:
            # Lazy import quality tools
            from app.services.crewai_flows.tools.data_validation_tool import (
                create_data_validation_tools,
            )

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
        tools_added = 0
        try:
            # Lazy import business analysis tools
            from app.services.crewai_flows.tools.dependency_analysis_tool import (
                create_dependency_analysis_tools,
            )
            from app.services.tools.asset_intelligence_tools import (
                get_asset_intelligence_tools,
            )

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

        tools_added = 0

        try:
            # Lazy import field mapping tools
            from app.services.crewai_flows.tools.mapping_confidence_tool import (
                MappingConfidenceTool,
            )
            from app.services.crewai_flows.tools.critical_attributes_tool import (
                create_critical_attributes_tools,
            )

            # Add mapping confidence tool
            if MappingConfidenceTool:
                tools.append(MappingConfidenceTool(context_info=context_info))
                tools_added += 1

            # Add critical attributes assessment tools for field mapper
            # This enables the agent to assess the 22 critical attributes
            tools_added += cls._safe_extend_tools(
                tools,
                create_critical_attributes_tools,
                "critical attributes",
                context_info,
            )

            logger.debug(
                f"Added {tools_added} field mapper tools including critical attributes assessment"
            )
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
            logger.warning(f"Skipping {tool_name} - getter is None or False")
            return 0

        try:
            # Check if getter function requires context_info parameter
            import inspect

            sig = inspect.signature(getter)
            params = sig.parameters

            logger.debug(f"Tool {tool_name} - signature params: {list(params.keys())}")

            # CC: Check if function requires registry parameter (for new tool pattern)
            if "registry" in params:
                # Extract service_registry from context_info if available
                service_registry = (
                    context_info.get("service_registry") if context_info else None
                )
                # Debug logging for ServiceRegistry
                logger.warning(
                    f"Tool {tool_name} requires registry parameter. "
                    f"ServiceRegistry available: {service_registry is not None}"
                )
                # Skip tools that require ServiceRegistry when none is available
                if service_registry is None:
                    logger.warning(
                        f"Skipping {tool_name} - ServiceRegistry not available. "
                        f"Context info keys: {list(context_info.keys()) if context_info else 'None'}"
                    )
                    return 0

                if "context_info" in params:
                    new_tools = getter(context_info, registry=service_registry)
                else:
                    new_tools = getter(registry=service_registry)
            elif "context_info" in params and context_info is not None:
                logger.debug(
                    f"Tool {tool_name} requires context_info - calling with context"
                )
                new_tools = getter(context_info)
            elif "field_mapper" in params:
                logger.debug(
                    f"Tool {tool_name} requires field_mapper - calling with None"
                )
                # CC: get_asset_intelligence_tools requires field_mapper parameter
                # Pass None as it's optional and tools work without it
                new_tools = getter(field_mapper=None)
            else:
                logger.debug(f"Tool {tool_name} requires no params - calling getter()")
                new_tools = getter()

            logger.info(
                f"Tool {tool_name} returned {len(new_tools) if new_tools else 0} tools"
            )

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
        """Get comprehensive toolset for agent type."""
        tools = []

        try:
            # Extract context information
            client_account_id, engagement_id, service_registry = (
                cls.extract_context_info(context_info)
            )

            # Debug logging for service registry
            logger.debug(
                f"Getting tools for {agent_type}. "
                f"ServiceRegistry available: {service_registry is not None}, "
                f"Context keys: {list(context_info.keys()) if context_info else 'None'}"
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
                "asset_inventory",
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
