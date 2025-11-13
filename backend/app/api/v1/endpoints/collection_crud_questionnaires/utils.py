"""
Utility functions for collection questionnaires.
Helper functions for data processing, field mapping, and analysis.

This module has been modularized - most functions moved to specialized modules.
All functions are re-exported here for backward compatibility.
"""

import logging
from typing import Optional

# Re-export all functions from modular files for backward compatibility
from app.api.v1.endpoints.collection_crud_questionnaires.gap_detection import (
    _check_missing_critical_fields,
    _assess_data_quality,
    VERIFICATION_FIELDS,
)
from app.api.v1.endpoints.collection_crud_questionnaires.eol_detection import (
    _determine_eol_status,
    EOL_OS_PATTERNS,
    EOL_TECH_PATTERNS,
)
from app.api.v1.endpoints.collection_crud_questionnaires.asset_serialization import (
    _analyze_selected_assets,
    _get_asset_raw_data_safely,
    _find_unmapped_attributes,
    _get_selected_application_info,
    _suggest_field_mapping,
)
from app.api.v1.endpoints.collection_crud_questionnaires.data_extraction import (
    _extract_questionnaire_data,
    _try_extract_from_wrapper,
    _find_questionnaires_in_result,
    _extract_from_agent_output,
    _generate_from_gap_analysis,
)

logger = logging.getLogger(__name__)


def _convert_template_field_to_question(
    field: dict, selected_application_name: Optional[str] = None
) -> dict:
    """Convert a template field to a questionnaire question format."""
    question = {
        "field_id": field["field_id"],
        "question_text": field["question_text"],
        "field_type": field["field_type"],
        "required": field["required"],
        "category": field["category"],
        "options": field.get("options", []),
        "help_text": field.get("help_text", ""),
        "multiple": field.get("multiple", False),
        "metadata": field.get("metadata", {}),
    }

    if selected_application_name:
        question["metadata"]["asset_name"] = selected_application_name
        if field["field_id"] in ("application_name", "asset_name"):
            question["default_value"] = selected_application_name

    if field.get("default_value"):
        question["default_value"] = field["default_value"]

    return question


# Export all public functions
__all__ = [
    # Gap detection
    "_check_missing_critical_fields",
    "_assess_data_quality",
    "VERIFICATION_FIELDS",
    # EOL detection
    "_determine_eol_status",
    "EOL_OS_PATTERNS",
    "EOL_TECH_PATTERNS",
    # Asset serialization
    "_analyze_selected_assets",
    "_get_asset_raw_data_safely",
    "_find_unmapped_attributes",
    "_get_selected_application_info",
    "_suggest_field_mapping",
    # Data extraction
    "_extract_questionnaire_data",
    "_try_extract_from_wrapper",
    "_find_questionnaires_in_result",
    "_extract_from_agent_output",
    "_generate_from_gap_analysis",
    # Local utilities
    "_convert_template_field_to_question",
]
