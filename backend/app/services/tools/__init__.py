"""
External Tools Package for AI Agents
Contains tools that agents can use to interact with external systems and learn from data.
"""

from .field_mapping_tool import field_mapping_tool
from .registry import tool_registry, ToolMetadata
from .factory import tool_factory
from .base_tool import BaseDiscoveryTool, AsyncBaseDiscoveryTool
from .categories import TOOL_CATEGORIES, get_tools_for_phase

# Auto-discover tools on import
try:
    from .schema_analyzer_tool import SchemaAnalyzerTool
    from .field_matcher_tool import FieldMatcherTool
    from .pii_scanner_tool import PIIScannerTool
    
    # Gap Analysis Tools
    from .gap_analysis_tools import (
        AttributeMapperTool,
        CompletenessAnalyzerTool,
        QualityScorerTool,
        GapIdentifierTool,
        ImpactCalculatorTool,
        EffortEstimatorTool,
        PriorityRankerTool,
        CollectionPlannerTool
    )
except ImportError as e:
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