"""
External Tools Package for AI Agents
Contains tools that agents can use to interact with external systems and learn from data.
"""

from .base_tool import AsyncBaseDiscoveryTool, BaseDiscoveryTool
from .categories import TOOL_CATEGORIES, get_tools_for_phase
from .factory import tool_factory
from .field_mapping_tool import field_mapping_tool
from .registry import ToolMetadata, tool_registry

# Auto-discover tools on import
# Note: Tools are auto-discovered and registered via registry
# Individual tool imports removed to avoid unused import warnings
try:
    # Tools will be discovered automatically via registry
    pass
except ImportError:
    pass  # Tools will be discovered automatically

__all__ = [
    "field_mapping_tool",
    "tool_registry",
    "tool_factory",
    "ToolMetadata",
    "BaseDiscoveryTool",
    "AsyncBaseDiscoveryTool",
    "TOOL_CATEGORIES",
    "get_tools_for_phase",
]
