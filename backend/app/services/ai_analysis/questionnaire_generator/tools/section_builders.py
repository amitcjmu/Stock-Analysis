"""
Section Builder Functions
Extracted from generation.py for modularization.
Contains logic for building questionnaire sections and organizing questions by category.
"""

import logging
from typing import Dict, Optional, Tuple, List

from .intelligent_options import (
    get_security_vulnerabilities_options,
    get_business_logic_complexity_options,
    get_change_tolerance_options,
    get_availability_requirements_options,
    get_security_compliance_requirements_options,
    get_eol_technology_assessment_options,
    infer_field_type_from_config,
    get_fallback_field_type_and_options,
)

logger = logging.getLogger(__name__)


def _check_context_aware_field(
    attr_name: str, asset_context: Dict
) -> Optional[Tuple[str, List]]:
    """Check if field has context-aware intelligent options.

    Args:
        attr_name: Field/attribute name
        asset_context: Dict with asset data for intelligent option generation

    Returns:
        Tuple of (field_type, options) if context-aware function exists, None otherwise
    """
    # Map field names to their intelligent option functions
    context_aware_handlers = {
        "security_vulnerabilities": get_security_vulnerabilities_options,
        "business_logic_complexity": get_business_logic_complexity_options,
        "change_tolerance": get_change_tolerance_options,
        "availability_requirements": get_availability_requirements_options,
        "security_compliance_requirements": get_security_compliance_requirements_options,
        "eol_technology_assessment": get_eol_technology_assessment_options,
    }

    handler = context_aware_handlers.get(attr_name)
    if handler:
        return handler(asset_context)
    return None


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


def determine_field_type_and_options(
    attr_name: str, asset_context: Optional[Dict] = None
) -> Tuple[str, List]:
    """Determine field type and options based on attribute name and asset context.

    Uses FIELD_OPTIONS from config.py as single source of truth.
    Falls back to heuristics only for unmapped fields.

    Args:
        attr_name: Field/attribute name (e.g., 'business_logic_complexity')
        asset_context: Optional dict with asset data including 'technology_stack', etc.

    Returns:
        Tuple of (field_type: str, options: list)
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

    # CRITICAL: Check for context-aware fields BEFORE FIELD_OPTIONS
    # This enables intelligent option ordering based on asset characteristics
    if asset_context:
        result = _check_context_aware_field(attr_name, asset_context)
        if result:
            return result

    # Check if field has predefined options in FIELD_OPTIONS
    if attr_name in FIELD_OPTIONS:
        options = FIELD_OPTIONS[attr_name]
        field_type = infer_field_type_from_config(
            attr_name, options, CRITICAL_ATTRIBUTES_CONFIG
        )
        return field_type, options

    # Fallback to heuristic matching for unmapped fields
    return get_fallback_field_type_and_options(attr_name)


def build_question_from_attribute(
    attr_name: str,
    attr_config: dict,
    asset_ids: list,
    asset_context: Optional[Dict] = None,
) -> dict:
    """Build a question object from an attribute definition.

    Args:
        attr_name: Name of the attribute (e.g., 'operating_system_version')
        attr_config: Configuration from CriticalAttributesDefinition
        asset_ids: List of asset IDs that need this attribute
        asset_context: Optional dict with asset data for intelligent option generation

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

    # CRITICAL FIX: Pass asset_context to enable intelligent EOL-aware options
    # This ensures security_vulnerabilities gets EOL-based option ordering
    field_type, options = determine_field_type_and_options(field_id, asset_context)

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


def group_attributes_by_category(
    missing_fields: dict,
    attribute_mapping: dict,
    assets_data: Optional[List[Dict]] = None,
) -> dict:
    """Group missing attributes by category, one question per unique attribute.

    Args:
        missing_fields: Dict mapping asset_id to list of missing attribute names
        attribute_mapping: Dict mapping attribute names to their configurations
        assets_data: Optional list of asset data dicts with context (eol_technology, etc.)

    Returns:
        Dict mapping category names to lists of question dicts
    """
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

    # Build asset context lookup by asset_id for intelligent option generation
    asset_context_by_id = {}
    if assets_data:
        for asset in assets_data:
            asset_id = asset.get("id") or asset.get("asset_id")
            if asset_id:
                asset_context_by_id[asset_id] = asset

    # Generate ONE question per unique attribute
    for attr_name, asset_ids in attr_to_assets.items():
        if attr_name in attribute_mapping:
            attr_config = attribute_mapping[attr_name]
            category = attr_config.get("category", "application")

            # Get asset context for the first asset (for intelligent options)
            # All assets needing the same attribute get the same question
            asset_context = None
            if asset_ids and asset_context_by_id:
                first_asset_id = asset_ids[0]
                asset_context = asset_context_by_id.get(first_asset_id)

            # Pass all asset IDs that need this attribute + asset context for intelligent options
            question = build_question_from_attribute(
                attr_name, attr_config, asset_ids, asset_context
            )
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
