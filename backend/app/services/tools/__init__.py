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
try:
    from .field_matcher_tool import FieldMatcherTool

    # Gap Analysis Tools
    from .gap_analysis_tools import (
        AttributeMapperTool,
        CollectionPlannerTool,
        CompletenessAnalyzerTool,
        EffortEstimatorTool,
        GapIdentifierTool,
        ImpactCalculatorTool,
        PriorityRankerTool,
        QualityScorerTool,
    )
    from .pii_scanner_tool import PIIScannerTool
    from .schema_analyzer_tool import SchemaAnalyzerTool
except ImportError:
    pass  # Tools will be discovered automatically

__all__ = [
    'field_mapping_tool',
    'tool_registry', 
    'tool_factory',
    'ToolMetadata',
    'BaseDiscoveryTool',
    'AsyncBaseDiscoveryTool',
    'TOOL_CATEGORIES',
    'get_tools_for_phase'
] 