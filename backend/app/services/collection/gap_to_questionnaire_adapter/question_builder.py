"""
Question Builder for Individual Gap-to-Question Transformation

Converts FieldGap objects into questionnaire question dictionaries.
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from app.services.gap_detection.schemas import FieldGap, GapPriority

logger = logging.getLogger(__name__)


class QuestionBuilder:
    """Builds individual questions from FieldGap objects."""

    def build_question_from_gap(
        self,
        gap: FieldGap,
        asset_id: UUID,
        asset_name: str,
        asset_type: str,
    ) -> Dict[str, Any]:
        """
        Build a question object directly from a gap.

        Uses gap metadata (field_name, priority, reason, layer) to create
        appropriate question text and field type.
        """
        field_name = gap.field_name
        readable_name = field_name.replace("_", " ").replace(".", " ").title()

        # Determine field type based on field name patterns
        field_type = "text"
        options = None

        # Check for common field patterns
        if any(x in field_name.lower() for x in ["criticality", "priority", "status"]):
            field_type = "select"
            options = self._get_options_for_field(field_name, asset_type)
        elif any(
            x in field_name.lower() for x in ["type", "category", "classification"]
        ):
            field_type = "select"
            options = self._get_options_for_field(field_name, asset_type)
        elif "version" in field_name.lower() or "version" in readable_name.lower():
            field_type = "text"  # Versions are free-form
        elif field_name in ["description", "notes", "comments"]:
            field_type = "textarea"
        elif any(
            x in field_name.lower() for x in ["count", "number", "cores", "gb", "mb"]
        ):
            field_type = "number"
        elif field_name.endswith("_id") or "uuid" in field_name.lower():
            field_type = "text"  # IDs are text

        # Build question text from gap reason if available
        question_text = gap.reason or f"What is the {readable_name}?"
        if not question_text.endswith("?"):
            question_text = f"{question_text}?"

        question = {
            "field_id": f"{asset_id}__{field_name}",  # Composite ID for asset-specific fields
            "question_text": question_text,
            "field_type": field_type,
            "required": gap.priority in [GapPriority.CRITICAL, GapPriority.HIGH],
            "category": gap.layer or "application",
            "metadata": {
                "asset_id": str(asset_id),
                "asset_name": asset_name,
                "gap_field_name": field_name,
                "gap_priority": (
                    gap.priority.value
                    if isinstance(gap.priority, GapPriority)
                    else str(gap.priority)
                ),
                "gap_layer": gap.layer,
                "gap_reason": gap.reason,
            },
            "help_text": f"Please provide the {readable_name.lower()} for {asset_name}.",
        }

        if options:
            question["options"] = options

        return question

    def _get_options_for_field(
        self, field_name: str, asset_type: str
    ) -> List[Dict[str, str]]:
        """Get options for select/dropdown fields based on field name."""
        field_lower = field_name.lower()

        if "criticality" in field_lower:
            return [
                {"value": "critical", "label": "Critical"},
                {"value": "high", "label": "High"},
                {"value": "medium", "label": "Medium"},
                {"value": "low", "label": "Low"},
            ]
        elif "type" in field_lower and "application" in field_lower:
            return [
                {"value": "web_application", "label": "Web Application"},
                {"value": "api_service", "label": "API Service"},
                {"value": "batch_job", "label": "Batch Job"},
                {"value": "database", "label": "Database"},
                {"value": "other", "label": "Other"},
            ]
        elif "status" in field_lower:
            return [
                {"value": "active", "label": "Active"},
                {"value": "inactive", "label": "Inactive"},
                {"value": "deprecated", "label": "Deprecated"},
                {"value": "decommissioned", "label": "Decommissioned"},
            ]

        return None


__all__ = ["QuestionBuilder"]
