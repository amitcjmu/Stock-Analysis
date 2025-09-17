"""
CrewAI Tool Implementations for Critical Attributes Assessment

Contains the actual CrewAI tool classes that agents can use to assess
critical attributes and calculate migration readiness scores.
"""

import json
import logging
from typing import Any, Dict, List

from .assessment import CriticalAttributesAssessor
from .base import CREWAI_TOOLS_AVAILABLE, BaseTool, CriticalAttributesDefinition
from .scoring import MigrationReadinessScorer

logger = logging.getLogger(__name__)


def create_critical_attributes_tools(context_info: Dict[str, Any]) -> List:
    """
    Create tools for agents to assess critical attributes and migration readiness

    Args:
        context_info: Dictionary containing client_account_id, engagement_id, flow_id

    Returns:
        List of critical attributes assessment tools
    """
    logger.info(
        "🔧 Creating critical attributes assessment tools for persistent agents"
    )

    if not CREWAI_TOOLS_AVAILABLE:
        logger.warning("⚠️ CrewAI tools not available - returning empty list")
        return []

    try:
        tools = []

        # Critical attributes assessor
        assessor = CriticalAttributesAssessmentTool(context_info)
        tools.append(assessor)

        # Migration readiness scorer
        scorer = MigrationReadinessScoreTool(context_info)
        tools.append(scorer)

        # Attribute mapping suggester
        suggester = AttributeMappingSuggestionTool(context_info)
        tools.append(suggester)

        logger.info(f"✅ Created {len(tools)} critical attributes tools")
        return tools
    except Exception as e:
        logger.error(f"❌ Failed to create critical attributes tools: {e}")
        return []


# CrewAI tool implementations
def _create_crewai_tool_classes():
    """Create CrewAI tool classes when CrewAI is available"""
    if not CREWAI_TOOLS_AVAILABLE:
        return _create_dummy_tool_classes()

    return {
        "CriticalAttributesAssessmentTool": _create_assessment_tool_class(),
        "MigrationReadinessScoreTool": _create_readiness_tool_class(),
        "AttributeMappingSuggestionTool": _create_suggestion_tool_class(),
    }


def _create_assessment_tool_class():
    """Create the critical attributes assessment tool class"""

    class CriticalAttributesAssessmentTool(BaseTool):
        """Tool for assessing critical attributes coverage"""

        name: str = "critical_attributes_assessor"
        description: str = """
        Assess the coverage of 22 critical attributes needed for 6R migration decisions.
        Use this tool to evaluate data completeness and migration readiness.

        Input: Dictionary with 'raw_data' (list of records) and optional 'field_mappings'
        Output: Assessment results with coverage metrics and recommendations
        """

        def __init__(self, context_info: Dict[str, Any]):
            super().__init__()
            self._context_info = context_info

        def _run(self, assessment_request: str) -> str:
            """Assess critical attributes coverage"""
            try:
                request = json.loads(assessment_request)
                raw_data = request.get("raw_data", [])
                field_mappings = request.get("field_mappings", {})

                result = CriticalAttributesAssessor.assess_data_coverage(
                    raw_data, field_mappings
                )
                return json.dumps(result)

            except Exception as e:
                logger.error(f"❌ Critical attributes assessment failed: {e}")
                return json.dumps({"error": str(e), "migration_readiness_score": 0})

    return CriticalAttributesAssessmentTool


def _create_readiness_tool_class():
    """Create the migration readiness scoring tool class"""

    class MigrationReadinessScoreTool(BaseTool):
        """Tool for calculating 6R migration readiness scores"""

        name: str = "migration_readiness_scorer"
        description: str = """
        Calculate migration readiness scores for each 6R strategy based on attribute coverage.
        Use this to recommend the best migration strategy.

        Input: Dictionary with 'attribute_coverage' from assessment and optional 'asset_data'
        Output: 6R readiness scores with strategy recommendations
        """

        def __init__(self, context_info: Dict[str, Any]):
            super().__init__()
            self._context_info = context_info

        def _run(self, scoring_request: str) -> str:
            """Calculate 6R readiness scores"""
            try:
                request = json.loads(scoring_request)
                attribute_coverage = request.get("attribute_coverage", {})
                asset_data = request.get("asset_data", {})

                result = MigrationReadinessScorer.calculate_sixr_readiness(
                    attribute_coverage, asset_data
                )
                return json.dumps(result)

            except Exception as e:
                logger.error(f"❌ Migration readiness scoring failed: {e}")
                return json.dumps({"error": str(e), "overall_readiness": 0})

    return MigrationReadinessScoreTool


def _create_suggestion_tool_class():
    """Create the attribute mapping suggestion tool class"""

    class AttributeMappingSuggestionTool(BaseTool):
        """Tool for suggesting field mappings to critical attributes"""

        name: str = "attribute_mapping_suggester"
        description: str = """
        Suggest field mappings from source data to the 22 critical attributes.
        Use this to improve attribute coverage and migration readiness.

        Input: Dictionary with 'source_fields' list
        Output: Mapping suggestions for critical attributes with confidence scores
        """

        def __init__(self, context_info: Dict[str, Any]):
            super().__init__()
            self._context_info = context_info

        def _run(self, suggestion_request: str) -> str:
            """Suggest critical attribute mappings"""
            try:
                request = json.loads(suggestion_request)
                source_fields = request.get("source_fields", [])
                suggestions = _generate_attribute_suggestions(source_fields)
                return json.dumps(suggestions)

            except Exception as e:
                logger.error(f"❌ Attribute mapping suggestion failed: {e}")
                return json.dumps({"error": str(e), "suggestions": {}})

    return AttributeMappingSuggestionTool


def _generate_attribute_suggestions(source_fields: List[str]) -> Dict[str, Any]:
    """Generate attribute mapping suggestions for given source fields"""
    attribute_mapping = CriticalAttributesDefinition.get_attribute_mapping()
    suggestions = {}

    for field in source_fields:
        field_lower = field.lower()
        best_match, best_confidence = _find_best_attribute_match(
            field_lower, attribute_mapping
        )

        if best_match:
            suggestions[field] = {
                "critical_attribute": best_match,
                "confidence": best_confidence,
                "category": attribute_mapping[best_match]["category"],
                "required": attribute_mapping[best_match]["required"],
            }

    return {
        "suggestions": suggestions,
        "total_fields": len(source_fields),
        "mapped_to_critical": len(suggestions),
        "coverage_improvement": len(suggestions) / 22 * 100,
    }


def _find_best_attribute_match(
    field_lower: str, attribute_mapping: Dict[str, Dict[str, Any]]
) -> tuple:
    """Find the best matching attribute for a given field"""
    best_match = None
    best_confidence = 0.0

    for attr_name, attr_config in attribute_mapping.items():
        for pattern in attr_config["patterns"]:
            if pattern in field_lower or field_lower in pattern:
                confidence = 0.9 if pattern == field_lower else 0.7
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = attr_name

    return best_match, best_confidence


def _create_dummy_tool_classes():
    """Create dummy tool classes when CrewAI is not available"""

    class CriticalAttributesAssessmentTool:
        def __init__(self, context_info: Dict[str, Any]):
            pass

    class MigrationReadinessScoreTool:
        def __init__(self, context_info: Dict[str, Any]):
            pass

    class AttributeMappingSuggestionTool:
        def __init__(self, context_info: Dict[str, Any]):
            pass

    return {
        "CriticalAttributesAssessmentTool": CriticalAttributesAssessmentTool,
        "MigrationReadinessScoreTool": MigrationReadinessScoreTool,
        "AttributeMappingSuggestionTool": AttributeMappingSuggestionTool,
    }


# Create tool classes based on CrewAI availability
_TOOL_CLASSES = _create_crewai_tool_classes()
CriticalAttributesAssessmentTool = _TOOL_CLASSES["CriticalAttributesAssessmentTool"]
MigrationReadinessScoreTool = _TOOL_CLASSES["MigrationReadinessScoreTool"]
AttributeMappingSuggestionTool = _TOOL_CLASSES["AttributeMappingSuggestionTool"]
