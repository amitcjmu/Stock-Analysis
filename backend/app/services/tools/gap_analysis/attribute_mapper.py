"""
Attribute Mapper Tool - Maps collected data fields to critical attributes framework
"""

import logging
from typing import Any, ClassVar, Dict, List

from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata

from .constants import ATTRIBUTE_PATTERNS

logger = logging.getLogger(__name__)


class AttributeMapperTool(AsyncBaseDiscoveryTool):
    """Maps collected data fields to critical attributes framework"""

    name: str = "attribute_mapper"
    description: str = "Map raw data fields to the 22 critical attributes framework"

    # Use the shared patterns from constants
    ATTRIBUTE_PATTERNS: ClassVar[Dict[str, List[str]]] = ATTRIBUTE_PATTERNS

    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        return ToolMetadata(
            name="attribute_mapper",
            description="Map raw data fields to the 22 critical attributes framework",
            tool_class=cls,
            categories=["gap_analysis", "attribute_mapping"],
            required_params=["data_fields"],
            optional_params=[],
            context_aware=True,
            async_tool=True,
        )

    async def arun(self, data_fields: List[str]) -> Dict[str, Any]:
        """Map data fields to critical attributes"""
        try:
            self.log_with_context(
                "info", f"Mapping {len(data_fields)} fields to critical attributes"
            )

            mapping_results = {
                "mapped_attributes": {},
                "unmapped_fields": [],
                "confidence_scores": {},
                "suggestions": [],
            }

            # Normalize field names for comparison
            normalized_fields = {
                field.lower().replace(" ", "_"): field for field in data_fields
            }

            # Map each critical attribute
            for attribute, patterns in self.ATTRIBUTE_PATTERNS.items():
                best_match = None
                best_score = 0.0

                for pattern in patterns:
                    pattern_lower = pattern.lower()

                    # Exact match
                    if pattern_lower in normalized_fields:
                        best_match = normalized_fields[pattern_lower]
                        best_score = 1.0
                        break

                    # Partial match scoring
                    for norm_field, original_field in normalized_fields.items():
                        score = self._calculate_similarity(pattern_lower, norm_field)
                        if (
                            score > best_score and score > 0.6
                        ):  # Threshold for consideration
                            best_match = original_field
                            best_score = score

                if best_match:
                    mapping_results["mapped_attributes"][attribute] = best_match
                    mapping_results["confidence_scores"][attribute] = best_score

                    if best_score < 0.8:
                        mapping_results["suggestions"].append(
                            {
                                "attribute": attribute,
                                "mapped_to": best_match,
                                "confidence": best_score,
                                "suggestion": "Consider manual verification due to lower confidence",
                            }
                        )

            # Identify unmapped fields
            mapped_fields = set(mapping_results["mapped_attributes"].values())
            mapping_results["unmapped_fields"] = [
                field for field in data_fields if field not in mapped_fields
            ]

            # Calculate coverage
            total_attributes = len(self.ATTRIBUTE_PATTERNS)
            mapped_count = len(mapping_results["mapped_attributes"])
            mapping_results["coverage_percentage"] = (
                mapped_count / total_attributes
            ) * 100

            self.log_with_context(
                "info",
                f"Mapped {mapped_count}/{total_attributes} attributes "
                f"({mapping_results['coverage_percentage']:.1f}% coverage)",
            )

            return mapping_results

        except Exception as e:
            self.log_with_context("error", f"Error in attribute mapping: {e}")
            return {"error": str(e)}

    def _calculate_similarity(self, pattern: str, field: str) -> float:
        """Calculate similarity score between pattern and field"""
        # Simple similarity based on common substrings
        if pattern in field or field in pattern:
            return 0.8

        # Check for common words
        pattern_words = set(pattern.split("_"))
        field_words = set(field.split("_"))
        common_words = pattern_words.intersection(field_words)

        if common_words:
            return len(common_words) / max(len(pattern_words), len(field_words))

        return 0.0
