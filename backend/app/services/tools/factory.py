"""
Tool Factory for dynamic tool creation and management
"""

import logging
from typing import Any, Dict, List, Optional

from app.services.tools.categories import get_tools_for_phase
from app.services.tools.registry import tool_registry

logger = logging.getLogger(__name__)


class ToolFactory:
    """
    Factory for creating and managing tools.
    Provides:
    - Dynamic tool creation
    - Phase-based tool sets
    - Tool configuration management
    """

    def __init__(self):
        self.registry = tool_registry
        self.tool_instances: Dict[str, Any] = {}

    def create_tool(self, tool_name: str, **config) -> Optional[Any]:
        """Create a single tool instance"""
        try:
            tool = self.registry.get_tool(tool_name, **config)
            if tool:
                self.tool_instances[tool_name] = tool
                logger.info(f"Created tool: {tool_name}")
            return tool
        except Exception as e:
            logger.error(f"Failed to create tool {tool_name}: {e}")
            return None

    def create_tools_for_phase(
        self, phase: str, additional_tools: Optional[List[str]] = None
    ) -> List[Any]:
        """Create all tools needed for a specific phase"""
        # Get standard tools for phase
        phase_tools = get_tools_for_phase(phase)

        # Add any additional requested tools
        if additional_tools:
            phase_tools.update(additional_tools)

        # Create tool instances
        tools = []
        for tool_name in phase_tools:
            tool = self.create_tool(tool_name)
            if tool:
                tools.append(tool)

        logger.info(f"Created {len(tools)} tools for phase {phase}")
        return tools

    def create_tools_for_agent(
        self, agent_name: str, required_tools: List[str]
    ) -> List[Any]:
        """Create tools required by a specific agent"""
        tools = []

        for tool_name in required_tools:
            # Check if already created
            if tool_name in self.tool_instances:
                tools.append(self.tool_instances[tool_name])
            else:
                tool = self.create_tool(tool_name)
                if tool:
                    tools.append(tool)

        logger.info(f"Created {len(tools)} tools for agent {agent_name}")
        return tools

    def get_tool_capabilities(self) -> Dict[str, List[str]]:
        """Get all available tools grouped by category"""
        capabilities = {}

        for category in self.registry.list_categories():
            tools = self.registry.get_tools_by_category(category)
            capabilities[category] = [tool.name for tool in tools]

        return capabilities


# Global factory instance
tool_factory = ToolFactory()
