"""
Section Builder Functions
Extracted from generation.py for modularization.
Contains logic for building questionnaire sections and organizing questions by category.
"""

import logging

logger = logging.getLogger(__name__)


def create_basic_info_section() -> dict:
    """Create basic information section.

    IMPORTANT: collection_date is now handled internally by the system
    and should not be requested from users. This function returns an
    empty section that will be filtered out during processing.
    """
    # Metadata like collection_date should be set server-side, not requested from users
    # Returning empty section which will be filtered out if no questions
    basic_questions = []

    return {
        "section_id": "basic_information",
        "section_title": "Basic Information",
        "section_description": "General information about the assets being collected",
        "questions": basic_questions,
    }


def determine_field_type_and_options(attr_name: str) -> tuple:
    """Determine field type and options based on attribute name.

    Uses FIELD_OPTIONS from config.py as single source of truth.
    Falls back to heuristics only for unmapped fields.
    """
    # Import FIELD_OPTIONS and CRITICAL_ATTRIBUTES_CONFIG
    try:
        from app.services.manual_collection.adaptive_form_service.config import (
            FIELD_OPTIONS,
            CRITICAL_ATTRIBUTES_CONFIG,
        )
    except ImportError:
        logger.warning("Could not import FIELD_OPTIONS, using fallback heuristics")
        FIELD_OPTIONS = {}
        CRITICAL_ATTRIBUTES_CONFIG = {}

    # First check if field has predefined options in FIELD_OPTIONS
    if attr_name in FIELD_OPTIONS:
        options = FIELD_OPTIONS[attr_name]

        # Determine field type from CRITICAL_ATTRIBUTES_CONFIG if available
        if attr_name in CRITICAL_ATTRIBUTES_CONFIG:
            field_type_enum = CRITICAL_ATTRIBUTES_CONFIG[attr_name].get("field_type")
            if field_type_enum:
                field_type = (
                    field_type_enum.value
                    if hasattr(field_type_enum, "value")
                    else str(field_type_enum)
                )
            else:
                # Infer from options count
                field_type = (
                    "multi_select"
                    if isinstance(options, list) and len(options) > 3
                    else "select"
                )
        else:
            # Infer from options count
            field_type = (
                "multi_select"
                if isinstance(options, list) and len(options) > 3
                else "select"
            )

        return field_type, options

    # Fallback to heuristic matching for unmapped fields
    field_type = "text"
    options = []

    if "criticality" in attr_name.lower():
        field_type = "select"
        options = ["Critical", "High", "Medium", "Low"]
    elif attr_name == "compliance_constraints":  # Explicit match only
        field_type = "multi_select"
        options = ["PCI-DSS", "HIPAA", "GDPR", "SOX", "ISO 27001", "None"]
    elif attr_name == "architecture_pattern":
        field_type = "select"
        options = [
            "Monolithic",
            "N-Tier",
            "Microservices",
            "Serverless",
            "Event-Driven",
        ]
    elif attr_name == "technology_stack":
        field_type = "text"
    elif "dependencies" in attr_name.lower():
        field_type = "multi_select"
        options = []

    return field_type, options


def build_question_from_attribute(
    attr_name: str, attr_config: dict, asset_ids: list
) -> dict:
    """Build a question object from an attribute definition.

    Args:
        attr_name: Name of the attribute (e.g., 'operating_system_version')
        attr_config: Configuration from CriticalAttributesDefinition
        asset_ids: List of asset IDs that need this attribute

    Returns:
        Question dictionary with proper category assignment
    """
    # CRITICAL FIX: Use the FIRST asset_field as field_id to match gap field_name
    # Gaps are created with database column names (e.g., "operating_system")
    # But critical attributes use different names (e.g., "operating_system_version")
    # The asset_fields list contains the actual database field names
    asset_fields = attr_config.get("asset_fields", [])
    field_id = asset_fields[0] if asset_fields else attr_name

    readable_name = attr_name.replace("_", " ").title()
    # CRITICAL FIX: Use field_id (database field name) instead of attr_name (critical attribute name)
    # This ensures FIELD_OPTIONS lookup uses correct key (e.g., "cpu_cores" not "cpu_memory_storage_specs")
    field_type, options = determine_field_type_and_options(field_id)

    # Get category from attribute config (NOT hardcoded)
    category = attr_config.get("category", "application")

    question = {
        "field_id": field_id,  # ← Use gap field_name, not critical attribute name
        "question_text": f"What is the {readable_name}?",
        "field_type": field_type,
        "required": attr_config.get("required", False),
        "category": category,  # Use category from CriticalAttributesDefinition
        "metadata": {
            "asset_ids": asset_ids,  # Track all assets needing this attribute
            "asset_fields": asset_fields,  # Store all mapped field names
            "critical_attribute_name": attr_name,  # Preserve original attribute name
            "applies_to_count": len(asset_ids),
        },
        "help_text": f"Provide details about {readable_name.lower()}",
    }

    if options:
        question["options"] = options

    return question


def group_attributes_by_category(missing_fields: dict, attribute_mapping: dict) -> dict:
    """Group missing attributes by category, one question per unique attribute."""
    attrs_by_category = {
        "infrastructure": [],
        "application": [],
        "business": [],
        "technical_debt": [],
    }

    # Track which attributes are needed and which assets need them
    attr_to_assets = {}
    for asset_id, attr_names in missing_fields.items():
        for attr_name in attr_names:
            if attr_name not in attr_to_assets:
                attr_to_assets[attr_name] = []
            attr_to_assets[attr_name].append(asset_id)

    # Generate ONE question per unique attribute
    for attr_name, asset_ids in attr_to_assets.items():
        if attr_name in attribute_mapping:
            attr_config = attribute_mapping[attr_name]
            category = attr_config.get("category", "application")
            # Pass all asset IDs that need this attribute
            question = build_question_from_attribute(attr_name, attr_config, asset_ids)
            attrs_by_category[category].append(question)

    return attrs_by_category


def create_category_sections(attrs_by_category: dict) -> list:
    """Create sections organized by category."""
    category_config = {
        "infrastructure": {
            "title": "Infrastructure Information",
            "description": (
                "Infrastructure specifications and resource details "
                "needed for 6R assessment"
            ),
        },
        "application": {
            "title": "Application Architecture",
            "description": (
                "Application architecture, technology stack, and integration details"
            ),
        },
        "business": {
            "title": "Business Context",
            "description": (
                "Business criticality, compliance requirements, and stakeholder information"
            ),
        },
        "technical_debt": {
            "title": "Technical Assessment",
            "description": (
                "Code quality, security vulnerabilities, and "
                "technology lifecycle assessment"
            ),
        },
    }

    sections = []
    for category in ["infrastructure", "application", "business", "technical_debt"]:
        if attrs_by_category[category]:
            config = category_config[category]
            sections.append(
                {
                    "section_id": f"section_{category}",
                    "section_title": config["title"],
                    "section_description": config["description"],
                    "questions": attrs_by_category[category],
                }
            )

    return sections


def create_fallback_section(missing_fields: dict) -> dict:
    """Create fallback section when critical attributes system is unavailable."""
    critical_questions = []
    for asset_id, fields in missing_fields.items():
        for field in fields:
            critical_questions.append(
                {
                    "field_id": field,
                    "question_text": f"Please provide {field.replace('_', ' ').title()}",
                    "field_type": "text",
                    "required": True,
                    "category": "critical_field",
                    "metadata": {"asset_id": asset_id},
                }
            )

    if critical_questions:
        return {
            "section_id": "critical_fields",
            "section_title": "Critical Missing Information",
            "section_description": "Please provide the following critical information",
            "questions": critical_questions,
        }
    return None
