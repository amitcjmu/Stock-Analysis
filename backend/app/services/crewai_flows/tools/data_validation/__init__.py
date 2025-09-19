"""
Data Validation Tools for CrewAI Agents

Modularized data validation tools that provide backward compatibility
with the original single-file interface.
"""

import logging
from typing import Any, Dict, List, Type

from .base_tools import (
    BaseDataQualityAssessmentTool,
    BaseDataStructureAnalyzerTool,
    BaseDataValidationTool,
    BaseFieldSuggestionTool,
    CREWAI_TOOLS_AVAILABLE,
    DummyDataQualityAssessmentTool,
    DummyDataStructureAnalyzerTool,
    DummyDataValidationTool,
    DummyFieldSuggestionTool,
)
from .implementations import (
    DataQualityImpl,
    DataStructureAnalyzerImpl,
    DataValidationToolImpl,
    FieldSuggestionImpl,
)

logger = logging.getLogger(__name__)

# Assign appropriate classes based on CrewAI availability
DataValidationTool: Type
DataStructureAnalyzerTool: Type
FieldSuggestionTool: Type
DataQualityAssessmentTool: Type

if CREWAI_TOOLS_AVAILABLE:
    DataValidationTool = BaseDataValidationTool
    DataStructureAnalyzerTool = BaseDataStructureAnalyzerTool
    FieldSuggestionTool = BaseFieldSuggestionTool
    DataQualityAssessmentTool = BaseDataQualityAssessmentTool
else:
    DataValidationTool = DummyDataValidationTool
    DataStructureAnalyzerTool = DummyDataStructureAnalyzerTool
    FieldSuggestionTool = DummyFieldSuggestionTool
    DataQualityAssessmentTool = DummyDataQualityAssessmentTool


def create_data_validation_tools(context_info: Dict[str, Any]) -> List:
    """
    Create tools for agents to validate and process imported data

    Args:
        context_info: Dictionary containing client_account_id,
                      engagement_id, flow_id

    Returns:
        List of data validation tools
    """
    logger.info("🔧 Creating data validation tools for persistent agents")

    if not CREWAI_TOOLS_AVAILABLE:
        logger.warning("⚠️ CrewAI tools not available - returning empty list")
        return []

    try:
        tools = []

        # Data validation tool
        validator = DataValidationTool(context_info)
        tools.append(validator)

        # Data structure analyzer
        analyzer = DataStructureAnalyzerTool(context_info)
        tools.append(analyzer)

        # Field suggestion tool
        field_suggester = FieldSuggestionTool(context_info)
        tools.append(field_suggester)

        # Data quality assessment tool
        quality_assessor = DataQualityAssessmentTool(context_info)
        tools.append(quality_assessor)

        logger.info(f"✅ Created {len(tools)} data validation tools")
        return tools
    except Exception as e:
        logger.error(f"❌ Failed to create data validation tools: {e}")
        return []


# Backward compatibility exports
__all__ = [
    "DataValidationTool",
    "DataStructureAnalyzerTool",
    "FieldSuggestionTool",
    "DataQualityAssessmentTool",
    "DataValidationToolImpl",
    "DataStructureAnalyzerImpl",
    "FieldSuggestionImpl",
    "DataQualityImpl",
    "create_data_validation_tools",
]
