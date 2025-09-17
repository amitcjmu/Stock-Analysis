"""
Critical Attributes Assessment Tool for 6R Decision Making

Modularized package that provides tools for persistent agents to assess the completeness
of critical attributes needed for 6R migration strategy decisions.

This package maintains perfect backward compatibility with the original monolithic file.
All existing imports will continue to work exactly as before.
"""

# Import all classes and functions from the modular structure
from .assessment import CriticalAttributesAssessor
from .base import CREWAI_TOOLS_AVAILABLE, BaseTool, CriticalAttributesDefinition
from .scoring import MigrationReadinessScorer
from .tools import (
    AttributeMappingSuggestionTool,
    CriticalAttributesAssessmentTool,
    MigrationReadinessScoreTool,
    _create_crewai_tool_classes,
    _create_dummy_tool_classes,
    _find_best_attribute_match,
    _generate_attribute_suggestions,
    create_critical_attributes_tools,
)

# Re-export all public APIs to maintain backward compatibility
__all__ = [
    # Core classes - these were the main public APIs from the original file
    "CriticalAttributesDefinition",
    "CriticalAttributesAssessor",
    "MigrationReadinessScorer",
    # CrewAI tool classes - available when CrewAI is imported
    "CriticalAttributesAssessmentTool",
    "MigrationReadinessScoreTool",
    "AttributeMappingSuggestionTool",
    # Factory function - main entry point for tool creation
    "create_critical_attributes_tools",
    # Base utilities
    "BaseTool",
    "CREWAI_TOOLS_AVAILABLE",
    # Internal functions - made available for existing code that may import them
    "_create_crewai_tool_classes",
    "_create_dummy_tool_classes",
    "_generate_attribute_suggestions",
    "_find_best_attribute_match",
]

# Import logging for consistency with original module
import logging

logger = logging.getLogger(__name__)

# Module-level docstring content exactly as in original
__doc__ = """
Critical Attributes Assessment Tool for 6R Decision Making

Provides tools for persistent agents to assess the completeness of critical
attributes needed for 6R migration strategy decisions.
"""
