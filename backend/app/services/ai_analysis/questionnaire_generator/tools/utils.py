"""
Utility functions for questionnaire generation tools.
Factory functions and helper utilities.
"""

from typing import List, Any, Dict, Optional

from .generation import QuestionnaireGenerationTool
from .analysis import GapAnalysisTool
from .validation import AssetIntelligenceTool


def create_questionnaire_generation_tools(
    context_info: Optional[Dict[str, Any]] = None,
) -> List[Any]:
    """
    Create and return all questionnaire generation tools.

    Args:
        context_info: Optional context information (not currently used by these tools)

    Returns:
        List of instantiated questionnaire generation tools
    """
    return [
        QuestionnaireGenerationTool(),
        GapAnalysisTool(),
        AssetIntelligenceTool(),
    ]


def create_gap_analysis_tools(
    context_info: Optional[Dict[str, Any]] = None,
) -> List[Any]:
    """
    Create and return gap analysis tools.

    Args:
        context_info: Optional context information (not currently used by these tools)

    Returns:
        List of instantiated gap analysis tools
    """
    return [
        GapAnalysisTool(),
        AssetIntelligenceTool(),
    ]
