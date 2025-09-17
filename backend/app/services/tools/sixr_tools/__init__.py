"""
6R Analysis Tools for CrewAI Agents.
Specialized tools for CMDB analysis, parameter scoring, question generation, and validation.

This modular package maintains 100% backward compatibility with the original sixr_tools.py file.
All existing imports will continue to work exactly as before.
"""

# Import all tools from their modular locations
from .analysis.cmdb_analysis import CMDBAnalysisTool, CMDBAnalysisInput
from .analysis.code_analysis import CodeAnalysisTool, CodeAnalysisInput
from .analysis.question_generation import (
    QuestionGenerationTool,
    QuestionGenerationInput,
)
from .evaluation.parameter_scoring import ParameterScoringTool, ParameterScoringInput
from .evaluation.recommendation_validation import (
    RecommendationValidationTool,
    RecommendationValidationInput,
)

# Import common utilities from core
from .core.base import BaseTool, logger, SIXR_AVAILABLE

# Backward compatibility: Preserve original tool registry
SIXR_TOOLS = {
    "cmdb_analysis": CMDBAnalysisTool,
    "parameter_scoring": ParameterScoringTool,
    "question_generation": QuestionGenerationTool,
    "code_analysis": CodeAnalysisTool,
    "recommendation_validation": RecommendationValidationTool,
}


def get_sixr_tools() -> list[BaseTool]:
    """Get all 6R analysis tools."""
    return [tool_class() for tool_class in SIXR_TOOLS.values()]


def get_tool_by_name(tool_name: str) -> BaseTool | None:
    """Get a specific tool by name."""
    tool_class = SIXR_TOOLS.get(tool_name)
    return tool_class() if tool_class else None


# Export all classes and functions for backward compatibility
__all__ = [
    # Tool classes
    "CMDBAnalysisTool",
    "ParameterScoringTool",
    "QuestionGenerationTool",
    "CodeAnalysisTool",
    "RecommendationValidationTool",
    # Input schemas
    "CMDBAnalysisInput",
    "ParameterScoringInput",
    "QuestionGenerationInput",
    "CodeAnalysisInput",
    "RecommendationValidationInput",
    # Utility functions
    "get_sixr_tools",
    "get_tool_by_name",
    # Registry and constants
    "SIXR_TOOLS",
    "SIXR_AVAILABLE",
    # Base classes
    "BaseTool",
    "logger",
]
