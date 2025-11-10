"""
Assessment Question Builder Functions
Generates MCQ questions for data quality, dependencies, and technical assessments.
Part of Issue #980 questionnaire generation system.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def generate_data_quality_question(
    asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate question for data quality issue with MCQ format."""
    asset_name = asset_context.get("asset_name", "the asset")
    quality_issue = asset_context.get("quality_issue", "data quality concern")
    asset_id = asset_context.get("asset_id", "unknown")

    # ✅ FIX 0.4: Use composite field_id format (Issue #980)
    return {
        "field_id": f"{asset_id}__data_quality",
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
        "asset_id": asset_id,
        "metadata": {
            "asset_id": asset_id,
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
    asset_id = asset_context.get("asset_id", "unknown")

    # ✅ FIX 0.4: Use composite field_id format (Issue #980)
    return {
        "field_id": f"{asset_id}__dependencies",
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
        "asset_id": asset_id,
        "metadata": {
            "asset_id": asset_id,
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
    asset_id = asset_context.get("asset_id", "unknown")

    # ✅ FIX 0.4: Use composite field_id format (Issue #980)
    return {
        "field_id": f"{asset_id}__technical",
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
        "asset_id": asset_id,
        "metadata": {
            "asset_id": asset_id,
            "asset_name": asset_name,
            "modernization_readiness": "assessment_required",
        },
    }


def generate_generic_question(
    gap_type: str, asset_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate data collection question for unknown gap types with intelligent MCQ options.

    CRITICAL FIX (FIX 0.6 - QA Bug #2): This generates questions to COLLECT ACTUAL DATA VALUES,
    not to assess data availability status.

    QA Bug #2: Questions were asking "What is the status of X?" (available/partial/not_available)
    instead of "What is X?" with actual value options.
    """
    asset_name = asset_context.get("asset_name", "the asset")
    asset_id = asset_context.get("asset_id", "unknown")

    # Map common field names to intelligent MCQ options
    field_options = {
        "application_type": {
            "type": "select",
            "options": [
                {"value": "web_application", "label": "Web Application"},
                {"value": "api_service", "label": "API Service / REST API"},
                {"value": "database", "label": "Database"},
                {"value": "batch_processing", "label": "Batch Processing / ETL"},
                {"value": "microservice", "label": "Microservice"},
                {"value": "monolithic", "label": "Monolithic Application"},
                {"value": "middleware", "label": "Middleware / Integration Layer"},
                {"value": "mobile_backend", "label": "Mobile Backend"},
                {"value": "desktop_application", "label": "Desktop Application"},
                {"value": "other", "label": "Other - Please Specify"},
            ],
        },
        "canonical_name": {
            "type": "text",
            "options": None,
            "help_text": "Enter the official/canonical name for this asset (e.g., 'CustomerOrderingService')",
        },
        "description": {
            "type": "textarea",
            "options": None,
            "help_text": "Provide a brief description of this asset's purpose and functionality",
        },
        "business_criticality": {
            "type": "select",
            "options": [
                {
                    "value": "mission_critical",
                    "label": "Mission Critical (Revenue Generating)",
                },
                {
                    "value": "business_critical",
                    "label": "Business Critical (Operations Dependent)",
                },
                {"value": "important", "label": "Important (Business Supporting)"},
                {"value": "standard", "label": "Standard (Operational Support)"},
                {
                    "value": "low",
                    "label": "Low Priority (Development/Testing)",
                },
            ],
        },
    }

    # Get field-specific configuration or use text input as default
    field_config = field_options.get(
        gap_type,
        {
            "type": "text",
            "options": None,
            "help_text": f"Provide {gap_type.replace('_', ' ')} information for {asset_name}",
        },
    )

    question = {
        "field_id": f"{asset_id}__{gap_type}",
        "question_text": f"What is the {gap_type.replace('_', ' ')} for {asset_name}?",
        "field_type": field_config["type"],
        "required": True,
        "category": "general",
        "help_text": field_config.get(
            "help_text", f"Provide details about {gap_type.replace('_', ' ')}"
        ),
        "priority": "medium",
        "gap_type": gap_type,
        "asset_specific": True,
        "asset_id": asset_id,
        "metadata": {
            "asset_id": asset_id,
            "asset_name": asset_name,
            "gap_category": gap_type,
        },
    }

    if field_config["options"]:
        question["options"] = field_config["options"]

    return question


def generate_fallback_question(
    gap_type: str, asset_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate fallback question when generation fails with MCQ format."""
    asset_name = asset_context.get("asset_name", "the asset")
    asset_id = asset_context.get("asset_id", "unknown")

    # ✅ FIX 0.4: Use composite field_id format (Issue #980)
    return {
        "field_id": f"{asset_id}__fallback_{gap_type}",
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
        "asset_id": asset_id,
        "help_text": f"Assess overall information completeness for migration planning (fallback for {gap_type})",
        "metadata": {
            "asset_id": asset_id,
            "asset_name": asset_name,
            "fallback_for_gap_type": gap_type,
        },
    }
