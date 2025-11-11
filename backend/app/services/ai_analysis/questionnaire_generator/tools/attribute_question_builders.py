"""
Attribute Question Builder Functions
Generates questions for missing critical fields based on Asset model attributes.
Part of Issue #980 questionnaire generation system.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def generate_missing_field_question(
    asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate question for missing critical field."""
    field_name = asset_context.get("field_name", "unknown")
    asset_name = asset_context.get("asset_name", "the asset")

    # Map field names to user-friendly questions
    field_questions = {
        "business_owner": {
            "text": f"Who is the business owner responsible for {asset_name}?",
            "help_text": "Enter the name of the person or department that owns this asset "
            "from a business perspective",
            "type": "text",
            "validation": {"required": True, "min_length": 2},
        },
        "technical_owner": {
            "text": f"Who is the technical owner/team responsible for maintaining {asset_name}?",
            "help_text": "Enter the name of the technical team or individual responsible for this asset",
            "type": "text",
            "validation": {"required": True, "min_length": 2},
        },
        "six_r_strategy": {
            "text": f"What is the recommended migration strategy for {asset_name}?",
            "help_text": "Select the most appropriate migration strategy for this asset",
            "type": "select",
            "options": [
                {
                    "value": "rehost",
                    "label": "Rehost - Lift and Shift (P2V/V2V), IAAS",
                },
                {
                    "value": "replatform",
                    "label": "Replatform - PaaS/IAAS treatment, containerize",
                },
                {
                    "value": "refactor",
                    "label": "Refactor - Modify code for cloud VM/container deployment",
                },
                {
                    "value": "rearchitect",
                    "label": "Rearchitect - Cloud native services, microservices",
                },
                {"value": "replace", "label": "Replace - Replace with COTS/SaaS"},
                {
                    "value": "rewrite",
                    "label": "Rewrite - Rewrite in cloud native code",
                },
            ],
            "validation": {"required": True},
        },
        "migration_complexity": {
            "text": f"How complex is the migration for {asset_name}?",
            "help_text": "Assess the complexity based on dependencies, architecture, and technical debt",
            "type": "select",
            "options": [
                {
                    "value": "low",
                    "label": "Low - Simple migration with minimal dependencies",
                },
                {
                    "value": "medium",
                    "label": "Medium - Moderate complexity with some dependencies",
                },
                {
                    "value": "high",
                    "label": "High - Complex with many dependencies and technical challenges",
                },
                {
                    "value": "very_high",
                    "label": "Very High - Extremely complex requiring significant refactoring",
                },
            ],
            "validation": {"required": True},
        },
        "dependencies": {
            "text": f"What are the key dependencies for {asset_name}?",
            "help_text": (
                "List other systems, databases, or services that this asset depends on or that depend on it"
            ),
            "type": "textarea",
            "validation": {"required": True, "min_length": 10},
        },
        "operating_system": {
            "text": f"What operating system does {asset_name} run on?",
            "help_text": "Specify the operating system and version if known",
            "type": "text",
            "validation": {"required": True, "min_length": 2},
        },
    }

    question_config = field_questions.get(
        field_name,
        {
            "text": f"Please provide information for the {field_name.replace('_', ' ')} field for {asset_name}",
            "help_text": f"This information is needed for {field_name.replace('_', ' ')}",
            "type": "text",
            "validation": {"required": True},
        },
    )

    # ✅ FIX 0.4: Use composite field_id format {asset_id}__{field_name} (Issue #980)
    # This matches the format expected by gap resolution and asset writeback
    asset_id = asset_context.get("asset_id", "unknown")
    composite_field_id = f"{asset_id}__{field_name}"

    return {
        "field_id": composite_field_id,  # ✅ Composite ID for multi-asset forms
        "question_text": question_config["text"],
        "field_type": question_config["type"],
        "required": question_config.get("validation", {}).get("required", True),
        "category": "missing_field",
        "options": question_config.get("options", []),
        "help_text": question_config["help_text"],
        "validation_rules": question_config.get("validation", {}),
        "priority": "high",
        "gap_type": "missing_field",
        "asset_specific": True,
        "asset_id": asset_id,
        "metadata": {
            "field_name": field_name,
            "asset_name": asset_name,
            "gap_category": "missing_critical_field",
        },
    }


def generate_unmapped_attribute_question(
    asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate question for unmapped attribute."""
    attribute_name = asset_context.get("attribute_name", "unknown")
    attribute_value = asset_context.get("attribute_value", "")
    asset_name = asset_context.get("asset_name", "the asset")
    suggested_mapping = asset_context.get("suggested_mapping", "custom_field")
    asset_id = asset_context.get("asset_id", "unknown")

    # ✅ FIX 0.4: Use composite field_id format (Issue #980)
    return {
        "field_id": f"{asset_id}__unmapped_{attribute_name}",
        "question_text": (
            f"How should the '{attribute_name}' field (value: '{str(attribute_value)[:50]}...') "
            f"be mapped for {asset_name}?"
        ),
        "field_type": "select",
        "required": False,
        "category": "data_mapping",
        "options": [
            {
                "value": suggested_mapping,
                "label": f"Map to {suggested_mapping.replace('_', ' ')}",
            },
            {"value": "custom_attribute", "label": "Store as custom attribute"},
            {"value": "ignore", "label": "Ignore this field"},
            {"value": "manual_review", "label": "Requires manual review"},
        ],
        "help_text": f"This field was found in the imported data but wasn't automatically mapped. "
        f"Suggested mapping: {suggested_mapping}",
        "priority": "medium",
        "gap_type": "unmapped_attribute",
        "asset_specific": True,
        "asset_id": asset_id,
        "metadata": {
            "attribute_name": attribute_name,
            "attribute_value": str(attribute_value)[:100],
            "suggested_mapping": suggested_mapping,
        },
    }
