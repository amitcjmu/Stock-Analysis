"""
Agent Tools Management Module

This module contains tool management functionality extracted from
tenant_scoped_agent_pool.py to reduce file length and improve maintainability.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.service_registry import ServiceRegistry

logger = logging.getLogger(__name__)


class AgentToolsManager:
    """Manages tools for agents based on their type and context"""

    @classmethod
    def add_tools_with_registry(
        cls,
        context_info: Dict[str, Any],
        tools: List,
        service_registry: "ServiceRegistry",
    ) -> List:
        """Add tools to agent using service registry with robust error handling"""
        try:
            agent_type = context_info.get("agent_type", "unknown")

            # Add agent-specific tools based on type
            cls._add_agent_specific_tools(context_info, tools, service_registry)

            # Add legacy tools as fallback
            cls._add_legacy_tools(tools)

            logger.debug(f"✅ Added {len(tools)} tools for {agent_type} agent")
            return tools

        except Exception as e:
            logger.error(f"❌ Failed to add tools with registry: {e}")
            # Return empty tools list on error
            return []

    @classmethod
    def _add_agent_specific_tools(
        cls,
        context_info: Dict[str, Any],
        tools: List,
        service_registry: "ServiceRegistry",
    ):
        """Add tools specific to the agent type"""
        agent_type = context_info.get("agent_type", "")

        if agent_type == "data_analyst":
            cls._add_data_analysis_tools(context_info, tools, service_registry)
        elif agent_type == "quality_assessor":
            cls._add_quality_tools(context_info, tools)
        elif agent_type == "business_value_analyst":
            cls._add_business_analysis_tools(context_info, tools, service_registry)
        elif agent_type == "field_mapper":
            cls._add_field_mapper_tools(context_info, tools)
        elif agent_type == "risk_assessment_agent":
            cls._add_risk_assessment_tools(context_info, tools, service_registry)
        elif agent_type == "pattern_discovery_agent":
            cls._add_pattern_discovery_tools(context_info, tools, service_registry)
        elif agent_type == "recommendation_generator":
            cls._add_recommendation_generator_tools(
                context_info, tools, service_registry
            )
        else:
            logger.debug(f"No specific tools defined for agent type: {agent_type}")

    @classmethod
    def _add_data_analysis_tools(
        cls,
        context_info: Dict[str, Any],
        tools: List,
        service_registry: "ServiceRegistry",
    ) -> None:
        """Add data analysis specific tools"""
        added_count = 0

        # Data validation tools
        added_count += cls._safe_extend_tools(
            tools,
            lambda: service_registry.get_data_validation_tools(),
            "data_validation_tools",
        )

        # Asset intelligence tools
        added_count += cls._safe_extend_tools(
            tools,
            lambda: service_registry.get_asset_intelligence_tools(),
            "asset_intelligence_tools",
        )

        # Statistical analysis tools
        added_count += cls._safe_extend_tools(
            tools,
            lambda: service_registry.get_statistical_analysis_tools(),
            "statistical_analysis_tools",
        )

        logger.debug(f"Added {added_count} data analysis tools")

    @classmethod
    def _add_quality_tools(cls, context_info: Dict[str, Any], tools: List) -> None:
        """Add quality assessment tools"""
        # Placeholder for quality-specific tools
        logger.debug("Quality tools placeholder - implement specific tools as needed")

    @classmethod
    def _add_business_analysis_tools(
        cls,
        context_info: Dict[str, Any],
        tools: List,
        service_registry: "ServiceRegistry",
    ) -> None:
        """Add business analysis specific tools"""
        added_count = 0

        # Business value analysis tools
        added_count += cls._safe_extend_tools(
            tools,
            lambda: service_registry.get_business_analysis_tools(),
            "business_analysis_tools",
        )

        # Cost estimation tools
        added_count += cls._safe_extend_tools(
            tools,
            lambda: service_registry.get_cost_estimation_tools(),
            "cost_estimation_tools",
        )

        logger.debug(f"Added {added_count} business analysis tools")

    @classmethod
    def _add_field_mapper_tools(cls, context_info: Dict[str, Any], tools: List) -> None:
        """Add field mapping specific tools"""
        # Field mapping tools would be added here
        # For now, just log that this is a placeholder
        logger.debug("Field mapper tools placeholder - implement as needed")

    @classmethod
    def _add_risk_assessment_tools(
        cls,
        context_info: Dict[str, Any],
        tools: List,
        service_registry: "ServiceRegistry",
    ) -> None:
        """Add risk assessment specific tools"""
        added_count = 0

        # Risk analysis tools
        added_count += cls._safe_extend_tools(
            tools,
            lambda: service_registry.get_risk_analysis_tools(),
            "risk_analysis_tools",
        )

        logger.debug(f"Added {added_count} risk assessment tools")

    @classmethod
    def _add_pattern_discovery_tools(
        cls,
        context_info: Dict[str, Any],
        tools: List,
        service_registry: "ServiceRegistry",
    ) -> None:
        """Add pattern discovery specific tools"""
        added_count = 0

        # Pattern analysis tools
        added_count += cls._safe_extend_tools(
            tools,
            lambda: service_registry.get_pattern_analysis_tools(),
            "pattern_analysis_tools",
        )

        logger.debug(f"Added {added_count} pattern discovery tools")

    @classmethod
    def _add_recommendation_generator_tools(
        cls,
        context_info: Dict[str, Any],
        tools: List,
        service_registry: "ServiceRegistry",
    ) -> None:
        """Add recommendation generator specific tools for 6R strategy and wave planning"""
        added_count = 0

        # Asset intelligence tools for asset data access
        try:
            from app.services.tools.asset_intelligence_tools import (
                get_asset_intelligence_tools,
            )

            added_count += cls._safe_extend_tools(
                tools,
                lambda: get_asset_intelligence_tools(),
                "asset_intelligence_tools",
            )
        except ImportError as e:
            logger.warning(f"Failed to import asset_intelligence_tools: {e}")

        # Dependency analysis tools for wave planning and dependency mapping
        try:
            from app.services.crewai_flows.tools.dependency_analysis_tool.factory import (
                create_dependency_analysis_tools,
            )

            added_count += cls._safe_extend_tools(
                tools,
                lambda: create_dependency_analysis_tools(context_info),
                "dependency_analysis_tools",
            )
        except ImportError as e:
            logger.warning(f"Failed to import dependency_analysis_tools: {e}")

        # Critical attributes tools for readiness assessment
        try:
            from app.services.crewai_flows.tools.critical_attributes_tool.tools import (
                create_critical_attributes_tools,
            )

            added_count += cls._safe_extend_tools(
                tools,
                lambda: create_critical_attributes_tools(context_info),
                "critical_attributes_tools",
            )
        except ImportError as e:
            logger.warning(f"Failed to import critical_attributes_tools: {e}")

        logger.debug(f"Added {added_count} recommendation generator tools")

    @classmethod
    def _add_legacy_tools(cls, tools: List):
        """Add legacy tools as fallback"""
        try:
            # Import and add legacy tools if available
            from app.services.tools import get_legacy_agent_tools

            legacy_tools = get_legacy_agent_tools()
            if legacy_tools:
                tools.extend(legacy_tools)
                logger.debug(f"Added {len(legacy_tools)} legacy tools")
        except ImportError:
            # Legacy tools not available - this is fine
            logger.debug("Legacy tools not available")
        except Exception as e:
            logger.warning(f"Failed to load legacy tools: {e}")

    @classmethod
    def _safe_extend_tools(cls, tools: List, getter, tool_name: str = "tools") -> int:
        """Safely extend tools list with error handling"""
        try:
            new_tools = getter()
            if new_tools and isinstance(new_tools, list):
                original_count = len(tools)
                tools.extend(new_tools)
                added_count = len(tools) - original_count
                logger.debug(f"Added {added_count} {tool_name}")
                return added_count
        except Exception as e:
            logger.warning(f"Failed to add {tool_name}: {e}")
        return 0

    @classmethod
    def get_agent_tools(cls, agent_type: str, context_info: Dict[str, Any]) -> List:
        """Get tools for a specific agent type"""
        tools = []

        try:
            # Try to get service registry
            from app.services.service_registry import ServiceRegistry

            service_registry = ServiceRegistry.get_instance()

            if service_registry:
                cls.add_tools_with_registry(
                    {**context_info, "agent_type": agent_type}, tools, service_registry
                )
            else:
                logger.warning(
                    "Service registry not available, using legacy tools only"
                )
                cls._add_legacy_tools(tools)

        except Exception as e:
            logger.error(f"Failed to get tools for {agent_type}: {e}")
            # Return empty list on error
            tools = []

        return tools
