"""
Section Builder Functions
Extracted from generation.py for modularization.
Contains logic for building questionnaire sections and organizing questions by category.

✅ Issue #980 Integration: Uses intelligent MCQ question builders for all gap types.
Removed all legacy fallback code that generated generic text questions.
"""

import logging
from typing import Any, Dict, Optional, Tuple, List

from .intelligent_options import (
    get_security_vulnerabilities_options,
    get_business_logic_complexity_options,
    get_change_tolerance_options,
    get_availability_requirements_options,
    get_security_compliance_requirements_options,
    get_eol_technology_assessment_options,
    get_dependencies_options,
    infer_field_type_from_config,
    get_fallback_field_type_and_options,
)

# ✅ Issue #980: Import intelligent question builders for all gap types
from .question_builders import (
    generate_missing_field_question,
    generate_data_quality_question,
    generate_dependency_question,
    generate_generic_technical_question,
    generate_generic_question,
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
        "dependencies": get_dependencies_options,
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

    ✅ NOTE: This function is ONLY used for MAPPED critical attributes (the good path).
    For unmapped gaps, Issue #980 intelligent builders are now used instead.

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
    existing_value: Optional[Any] = None,
) -> dict:
    """Build a question object from an attribute definition.

    Args:
        attr_name: Name of the attribute (e.g., 'operating_system_version')
        attr_config: Configuration from CriticalAttributesDefinition
        asset_ids: List of asset IDs that need this attribute
        asset_context: Optional dict with asset data for intelligent option generation
        existing_value: Optional pre-filled value for verification fields

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

    # Fix #3: Add pre-filled value for verification fields (e.g., operating_system)
    # User can confirm or change the discovered value
    if existing_value is not None:
        question["default_value"] = existing_value
        question["metadata"]["pre_filled"] = True
        question["metadata"]["verification_required"] = True

    return question


def group_attributes_by_category(  # noqa: C901
    missing_fields: dict,
    attribute_mapping: dict,
    assets_data: Optional[List[Dict]] = None,
    existing_field_values: Optional[Dict[str, Dict[str, Any]]] = None,
) -> dict:
    """Group missing attributes by category, one question per unique attribute.

    Args:
        missing_fields: Dict mapping asset_id to list of missing attribute names
        attribute_mapping: Dict mapping attribute names to their configurations
        assets_data: Optional list of asset data dicts with context (eol_technology, etc.)
        existing_field_values: Optional dict mapping asset_id -> {attr_name: value} for pre-fill

    Returns:
        Dict mapping category names to lists of question dicts
    """
    # ✅ FIX: Added missing categories used by Issue #980 intelligent builders
    # QA Bug #1: KeyError when intelligent builders assigned to 'dependencies', 'data_validation', 'technical_details'
    attrs_by_category = {
        "infrastructure": [],
        "application": [],
        "business": [],
        "technical_debt": [],
        "dependencies": [],  # Used by generate_dependency_question()
        "data_validation": [],  # Used by generate_data_quality_question()
        "technical_details": [],  # Used by generate_generic_technical_question()
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
        # CRITICAL FIX: Check both direct key match AND asset_fields match
        # Gap field names (e.g., "description", "application_type") might not match
        # critical attribute names (e.g., "business_criticality_score") directly,
        # but they might be in the asset_fields list of a critical attribute
        attr_config = None
        matched_attr_name = None

        # First, try direct key match
        if attr_name in attribute_mapping:
            attr_config = attribute_mapping[attr_name]
            matched_attr_name = attr_name
        else:
            # Second, search through all attributes to find one where attr_name is in asset_fields
            for critical_attr_name, config in attribute_mapping.items():
                asset_fields = config.get("asset_fields", [])
                if attr_name in asset_fields:
                    attr_config = config
                    matched_attr_name = critical_attr_name
                    logger.debug(
                        f"Matched gap field '{attr_name}' to critical attribute '{critical_attr_name}' "
                        f"via asset_fields: {asset_fields}"
                    )
                    break

        if attr_config:
            category = attr_config.get("category", "application")

            # Get asset context for the first asset (for intelligent options)
            # All assets needing the same attribute get the same question
            asset_context = None
            if asset_ids and asset_context_by_id:
                first_asset_id = asset_ids[0]
                asset_context = asset_context_by_id.get(first_asset_id)

            # Fix #3: Check for existing value for pre-fill (verification fields)
            # e.g., operating_system_version with discovered "AIX 7.2" -> pre-select in dropdown
            existing_value = None
            if existing_field_values and asset_ids:
                first_asset_id = asset_ids[0]
                if first_asset_id in existing_field_values:
                    existing_value = existing_field_values[first_asset_id].get(
                        attr_name
                    )

            # Pass all asset IDs that need this attribute + asset context for intelligent options
            # Use matched_attr_name (critical attribute name) for question generation,
            # but field_id will be set to attr_name (gap field name) in build_question_from_attribute
            question = build_question_from_attribute(
                matched_attr_name, attr_config, asset_ids, asset_context, existing_value
            )
            # CRITICAL FIX: Override field_id to use the gap field name, not the critical attribute name
            # This ensures the question maps back to the correct database column
            question["field_id"] = attr_name
            attrs_by_category[category].append(question)
        else:
            # ✅ Issue #980: Use intelligent MCQ question builders for gaps without critical attribute mapping
            # Instead of generic fallback, route to appropriate intelligent builder based on gap type
            logger.info(
                f"Gap field '{attr_name}' using Issue #980 intelligent builder for {len(asset_ids)} asset(s)"
            )

            # Build asset_context for intelligent builders (using first asset that has this gap)
            asset_context = {
                "field_name": attr_name,
                "asset_name": "the asset",  # Generic, will be made specific per asset
                "asset_id": asset_ids[0] if asset_ids else "unknown",
            }

            # Add asset-specific context if available
            if asset_ids and asset_context_by_id:
                first_asset_context = asset_context_by_id.get(asset_ids[0])
                if first_asset_context:
                    asset_context["asset_name"] = first_asset_context.get(
                        "asset_name", "the asset"
                    )
                    asset_context["operating_system"] = first_asset_context.get(
                        "operating_system"
                    )
                    asset_context["eol_technology"] = first_asset_context.get(
                        "eol_technology"
                    )

            # Route to appropriate Issue #980 intelligent builder based on field name patterns
            question = None

            # Dependency-related gaps
            if any(
                x in attr_name.lower()
                for x in ["dependency", "dependencies", "integration"]
            ):
                question = generate_dependency_question({}, asset_context)
                category = "dependencies"

            # Data quality gaps (low confidence from gap detection)
            elif "quality" in attr_name.lower() or "confidence" in attr_name.lower():
                asset_context["quality_issue"] = (
                    f"Low confidence in {attr_name.replace('_', ' ')}"
                )
                question = generate_data_quality_question({}, asset_context)
                category = "data_validation"

            # Technical/architecture gaps
            elif any(
                x in attr_name.lower()
                for x in ["technical", "architecture", "tech_debt", "modernization"]
            ):
                question = generate_generic_technical_question(asset_context)
                category = "technical_details"

            # Business/ownership gaps
            elif any(
                x in attr_name.lower() for x in ["business", "owner", "stakeholder"]
            ):
                question = generate_missing_field_question({}, asset_context)
                category = "business"

            # Infrastructure gaps
            elif any(
                x in attr_name.lower()
                for x in ["resilience", "availability", "disaster", "infrastructure"]
            ):
                question = generate_missing_field_question({}, asset_context)
                category = "infrastructure"

            # Generic gaps - use intelligent generic builder (MCQ with status options)
            else:
                question = generate_generic_question(attr_name, asset_context)
                category = "application"

            # Update field_id to non-composite format (single question for all assets)
            # Issue #980 builders use composite {asset_id}__{field},
            # but for cross-asset questions we use simple field_id
            question["field_id"] = attr_name

            # Update metadata to include all assets that need this field
            question["metadata"]["asset_ids"] = asset_ids
            question["metadata"]["applies_to_count"] = len(asset_ids)

            attrs_by_category[category].append(question)

    return attrs_by_category


def create_category_sections(attrs_by_category: dict) -> list:
    """Create sections organized by category.

    ✅ FIX: Added new categories from Issue #980 intelligent builders.
    """
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
        "dependencies": {
            "title": "Dependencies & Integrations",
            "description": (
                "System dependencies, integrations, and architectural complexity"
            ),
        },
        "data_validation": {
            "title": "Data Quality Verification",
            "description": (
                "Verify accuracy and completeness of discovered information"
            ),
        },
        "technical_details": {
            "title": "Technical Details",
            "description": (
                "Additional technical specifications and modernization readiness"
            ),
        },
    }

    sections = []
    # Process all categories (not just the original 4)
    for category in [
        "infrastructure",
        "application",
        "business",
        "technical_debt",
        "dependencies",
        "data_validation",
        "technical_details",
    ]:
        if attrs_by_category.get(category):  # Use .get() for safety
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


# ❌ REMOVED: create_fallback_section() - Legacy function that generated generic text questions
# Issue #980 intelligent MCQ builders are now fully integrated (see lines 291-355).
# All gap types now use proper MCQ questions with user-friendly text.
# If you see an error about missing create_fallback_section, it means legacy code is trying to use it.
# Solution: Update the calling code to use Issue #980's intelligent builders instead.
