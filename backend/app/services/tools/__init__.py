"""
External Tools Package for AI Agents
Contains tools that agents can use to interact with external systems and learn from data.
"""

# Import registry and categories first (no dependencies on tools)
from .registry import ToolMetadata, tool_registry
from .categories import TOOL_CATEGORIES, get_tools_for_phase
from .factory import tool_factory

# Import base tool classes after registry to avoid circular import
from .base_tool import AsyncBaseDiscoveryTool, BaseDiscoveryTool

# Import specific tools last
# REMOVED: field_mapping_tool
# from .field_mapping_tool import field_mapping_tool

# Auto-discover tools on import
# Note: Tools are auto-discovered and registered via registry
# Individual tool imports removed to avoid unused import warnings
try:
    # Initialize the tool registry to discover tools
    tool_registry.initialize()
except Exception:
    # Tools will be discovered later or on-demand
    pass

__all__ = [
    # REMOVED: "field_mapping_tool",
    "tool_registry",
    "tool_factory",
    "ToolMetadata",
    "BaseDiscoveryTool",
    "AsyncBaseDiscoveryTool",
    "TOOL_CATEGORIES",
    "get_tools_for_phase",
]
