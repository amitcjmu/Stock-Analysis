"""
Question Builder Functions
Extracted from generation.py for modularization.
Contains logic for generating different types of questionnaire questions.
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

    return {
        "field_id": field_name,
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
        "asset_id": asset_context.get("asset_id"),
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

    return {
        "field_id": f"unmapped_{attribute_name}",
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
        "asset_id": asset_context.get("asset_id"),
        "metadata": {
            "attribute_name": attribute_name,
            "attribute_value": str(attribute_value)[:100],
            "suggested_mapping": suggested_mapping,
        },
    }


def generate_data_quality_question(
    asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate question for data quality issue with MCQ format."""
    asset_name = asset_context.get("asset_name", "the asset")
    quality_issue = asset_context.get("quality_issue", "data quality concern")

    return {
        "field_id": f"data_quality_{asset_context.get('asset_id', 'unknown')}",
        "question_text": f"Data quality verification for {asset_name}: {quality_issue}",
        "field_type": "select",
        "required": True,
        "category": "data_validation",
        "options": [
            {
                "value": "verified_correct",
                "label": "Verified - Information is correct as discovered",
            },
            {
                "value": "needs_update",
                "label": "Needs Update - Information is outdated or incomplete",
            },
            {
                "value": "incorrect_high_confidence",
                "label": "Incorrect - Discovered data has high confidence issues",
            },
            {
                "value": "incorrect_low_confidence",
                "label": "Incorrect - Discovered data has low confidence",
            },
            {
                "value": "requires_manual_review",
                "label": "Requires Manual Review - Cannot verify at this time",
            },
        ],
        "help_text": (
            f"Data quality issue detected: {quality_issue}. "
            "Please verify the accuracy of the discovered information."
        ),
        "priority": "medium",
        "gap_type": "data_quality",
        "asset_specific": True,
        "asset_id": asset_context.get("asset_id"),
        "metadata": {
            "asset_id": asset_context.get("asset_id"),
            "asset_name": asset_name,
            "quality_issue": quality_issue,
            "gap_category": "data_quality_verification",
        },
    }


def generate_dependency_question(
    asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate question for dependency information with MCQ format."""
    asset_name = asset_context.get("asset_name", "the asset")

    return {
        "field_id": f"dependencies_{asset_context.get('asset_id', 'unknown')}",
        "question_text": f"What is the dependency complexity level for {asset_name}?",
        "field_type": "select",
        "required": True,
        "category": "dependencies",
        "options": [
            {
                "value": "minimal",
                "label": "Minimal - Standalone with no or few external dependencies",
            },
            {
                "value": "low",
                "label": "Low - Depends on 1-3 systems (e.g., single database, authentication service)",
            },
            {
                "value": "moderate",
                "label": "Moderate - Depends on 4-7 systems (e.g., multiple databases, APIs, message queues)",
            },
            {
                "value": "high",
                "label": "High - Depends on 8-15 systems with complex integration patterns",
            },
            {
                "value": "very_high",
                "label": "Very High - Highly coupled with 16+ systems, extensive service mesh",
            },
            {
                "value": "unknown",
                "label": "Unknown - Dependency analysis not yet performed",
            },
        ],
        "help_text": (
            "Assess the number and complexity of dependencies including "
            "databases, APIs, message queues, and other services."
        ),
        "priority": "high",
        "gap_type": "dependency",
        "asset_specific": True,
        "asset_id": asset_context.get("asset_id"),
        "metadata": {
            "asset_id": asset_context.get("asset_id"),
            "asset_name": asset_name,
            "dependency_type": "complexity_assessment",
            "analysis_required": True,
        },
    }


def generate_generic_technical_question(
    asset_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate generic technical question for unknown asset types with MCQ format."""
    asset_name = asset_context.get("asset_name", "the asset")

    return {
        "field_id": f"technical_{asset_context.get('asset_id', 'unknown')}",
        "question_text": f"What is the technical modernization readiness of {asset_name}?",
        "field_type": "select",
        "required": True,
        "category": "technical_details",
        "options": [
            {
                "value": "cloud_native",
                "label": "Cloud Native - Already containerized, microservices, cloud-ready",
            },
            {
                "value": "modernized",
                "label": "Modernized - Recent technology stack, well-architected, easy to migrate",
            },
            {
                "value": "legacy_supported",
                "label": "Legacy Supported - Older stack but still vendor-supported, moderate effort",
            },
            {
                "value": "legacy_unsupported",
                "label": "Legacy Unsupported - End-of-life technology, high migration complexity",
            },
            {
                "value": "mainframe_proprietary",
                "label": "Mainframe/Proprietary - Requires complete rewrite or replacement",
            },
            {
                "value": "unknown",
                "label": "Unknown - Technical assessment not yet completed",
            },
        ],
        "help_text": (
            "Assess the technical readiness and migration complexity based on "
            "technology stack, architecture, and modernization state"
        ),
        "priority": "medium",
        "gap_type": "technical_detail",
        "asset_specific": True,
        "asset_id": asset_context.get("asset_id"),
        "metadata": {
            "asset_id": asset_context.get("asset_id"),
            "asset_name": asset_name,
            "modernization_readiness": "assessment_required",
        },
    }


def generate_generic_question(
    gap_type: str, asset_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate generic question for unknown gap types with MCQ format."""
    asset_name = asset_context.get("asset_name", "the asset")

    return {
        "field_id": f"{gap_type}_{asset_context.get('asset_id', 'unknown')}",
        "question_text": f"What is the status of {gap_type.replace('_', ' ')} for {asset_name}?",
        "field_type": "select",
        "required": True,
        "category": "general",
        "options": [
            {
                "value": "available",
                "label": "Available - Information exists and is accessible",
            },
            {
                "value": "partial",
                "label": "Partially Available - Some information exists but incomplete",
            },
            {
                "value": "not_available",
                "label": "Not Available - Information needs to be gathered",
            },
            {
                "value": "not_applicable",
                "label": "Not Applicable - This attribute doesn't apply to this asset",
            },
            {
                "value": "unknown",
                "label": "Unknown - Assessment not yet completed",
            },
        ],
        "help_text": f"Assess the availability status of {gap_type.replace('_', ' ')} information",
        "priority": "medium",
        "gap_type": gap_type,
        "asset_specific": True,
        "asset_id": asset_context.get("asset_id"),
        "metadata": {
            "asset_id": asset_context.get("asset_id"),
            "asset_name": asset_name,
            "gap_category": gap_type,
        },
    }


def generate_fallback_question(
    gap_type: str, asset_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate fallback question when generation fails with MCQ format."""
    asset_name = asset_context.get("asset_name", "the asset")

    return {
        "field_id": f"fallback_{gap_type}_{asset_context.get('asset_id', 'unknown')}",
        "question_text": f"Information completeness for {asset_name}",
        "field_type": "select",
        "required": False,
        "category": "fallback",
        "options": [
            {
                "value": "complete",
                "label": "Complete - All required information is available",
            },
            {
                "value": "mostly_complete",
                "label": "Mostly Complete - Minor gaps but sufficient for planning",
            },
            {
                "value": "incomplete",
                "label": "Incomplete - Significant information gaps exist",
            },
            {
                "value": "requires_investigation",
                "label": "Requires Investigation - Major unknowns need to be researched",
            },
        ],
        "priority": "low",
        "asset_specific": True,
        "asset_id": asset_context.get("asset_id"),
        "help_text": f"Assess overall information completeness for migration planning (fallback for {gap_type})",
        "metadata": {
            "asset_id": asset_context.get("asset_id"),
            "asset_name": asset_name,
            "fallback_for_gap_type": gap_type,
        },
    }
