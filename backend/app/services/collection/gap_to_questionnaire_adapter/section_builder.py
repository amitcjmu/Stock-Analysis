"""
Section Builder for Grouping Questions by Layer

Organizes questions into logical sections based on gap layers.
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from app.services.gap_detection.schemas import FieldGap

from .question_builder import QuestionBuilder

logger = logging.getLogger(__name__)


class SectionBuilder:
    """Builds questionnaire sections by grouping gaps by layer."""

    def __init__(self, question_builder: QuestionBuilder):
        """Initialize with question builder dependency."""
        self.question_builder = question_builder

    def build_sections_from_gaps(
        self,
        gaps: List[FieldGap],
        asset_id: UUID,
        asset_name: str,
        asset_type: str,
    ) -> List[Dict[str, Any]]:
        """
        Build questionnaire sections directly from gap field names.

        Groups gaps by layer/category and creates questions for each gap.
        """
        # Group gaps by layer
        sections_by_layer = {
            "column": [],
            "jsonb": [],
            "enrichment": [],
            "application": [],
            "standards": [],
        }

        for gap in gaps:
            layer = gap.layer or "column"
            if layer not in sections_by_layer:
                layer = "column"  # Default fallback
            sections_by_layer[layer].append(gap)

        sections = []

        # Create section for each layer that has gaps
        layer_configs = self._get_layer_configs()

        for layer, layer_gaps in sections_by_layer.items():
            if not layer_gaps:
                continue

            config = layer_configs.get(layer, layer_configs["column"])
            questions = []

            for gap in layer_gaps:
                question = self.question_builder.build_question_from_gap(
                    gap, asset_id, asset_name, asset_type
                )
                questions.append(question)

            sections.append(
                {
                    "section_id": config["section_id"],
                    "section_title": config["section_title"],
                    "section_description": config["section_description"],
                    "questions": questions,
                }
            )

        return sections

    def _get_layer_configs(self) -> Dict[str, Dict[str, str]]:
        """Get configuration for each layer type."""
        return {
            "column": {
                "section_id": "asset_fields",
                "section_title": "Asset Information",
                "section_description": "Basic asset fields required for assessment",
            },
            "jsonb": {
                "section_id": "technical_details",
                "section_title": "Technical Details",
                "section_description": "Technical specifications and configuration details",
            },
            "enrichment": {
                "section_id": "enrichment_data",
                "section_title": "Enrichment Data",
                "section_description": "Additional enrichment data for assessment",
            },
            "application": {
                "section_id": "application_metadata",
                "section_title": "Application Metadata",
                "section_description": "Application-level metadata and information",
            },
            "standards": {
                "section_id": "compliance_standards",
                "section_title": "Compliance & Standards",
                "section_description": "Compliance and architectural standards information",
            },
        }


__all__ = ["SectionBuilder"]
