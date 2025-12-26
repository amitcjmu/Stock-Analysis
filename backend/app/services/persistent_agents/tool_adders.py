"""
Tool addition utilities for agent configuration.

Extracted from tool_manager.py for file length compliance.
Contains methods that add specific tool categories to agents.

Note: These methods are kept for backward compatibility but may not be used
in the current implementation.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ToolAdders:
    """Utility class for adding different categories of tools to agents."""

    @classmethod
    def add_data_analysis_tools(cls, context_info: Dict[str, Any], tools: List) -> int:
        """Add data analysis and validation tools - REMOVED: data validation tools."""
        tools_added = 0
        try:
            # REMOVED: Data validation tools
            # from app.services.crewai_flows.tools.data_validation_tool import (
            #     create_data_validation_tools,
            # )
            from app.services.crewai_flows.tools.critical_attributes_tool import (
                create_critical_attributes_tools,
            )

            from app.services.persistent_agents.tool_manager import AgentToolManager

            # tools_added += AgentToolManager._safe_extend_tools(
            #     tools, create_data_validation_tools, "data validation", context_info
            # )
            tools_added += AgentToolManager._safe_extend_tools(
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

            from app.services.persistent_agents.tool_manager import AgentToolManager

            tools_added += AgentToolManager._safe_extend_tools(
                tools,
                create_dependency_analysis_tools,
                "business dependency analysis",
                context_info,
            )
            tools_added += AgentToolManager._safe_extend_tools(
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
    def add_field_mapper_tools(cls, context_info: Dict[str, Any], tools: List) -> int:
        """Add field mapping specific tools - REMOVED: field mapping tools."""
        tools_added = 0

        try:
            # REMOVED: Field mapping tools
            # from app.services.crewai_flows.tools.mapping_confidence_tool import (
            #     MappingConfidenceTool,
            # )
            from app.services.crewai_flows.tools.critical_attributes_tool import (
                create_critical_attributes_tools,
            )

            from app.services.persistent_agents.tool_manager import AgentToolManager

            # REMOVED: Mapping confidence tool
            # if MappingConfidenceTool:
            #     tools.append(MappingConfidenceTool(context_info=context_info))
            #     tools_added += 1

            # Add critical attributes assessment tools for field mapper
            tools_added += AgentToolManager._safe_extend_tools(
                tools,
                create_critical_attributes_tools,
                "critical attributes",
                context_info,
            )

            logger.debug(
                f"Added {tools_added} field mapper tools including critical attributes"
            )
        except Exception as e:
            logger.warning(f"Failed to add field mapper tools: {e}")

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

            from app.services.persistent_agents.tool_manager import AgentToolManager

            # Add common legacy tools
            tools_added += AgentToolManager._safe_extend_tools(
                tools,
                create_asset_creation_tools,
                "legacy asset creation",
                context_info,
            )
            tools_added += AgentToolManager._safe_extend_tools(
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
    def add_quality_tools(cls, context_info: Dict[str, Any], tools: List) -> int:
        """Add quality assurance and validation tools."""
        tools_added = 0
        try:
            # Lazy import quality tools
            from app.services.crewai_flows.tools.data_validation_tool import (
                create_data_validation_tools,
            )

            from app.services.persistent_agents.tool_manager import AgentToolManager

            # Add quality-focused tools
            tools_added += AgentToolManager._safe_extend_tools(
                tools, create_data_validation_tools, "quality validation", context_info
            )
            logger.debug(f"Added {tools_added} quality tools")
        except Exception as e:
            logger.warning(f"Failed to add quality tools: {e}")

        return tools_added
