"""
Phase name alias system for backward compatibility
Per ADR-027: Support legacy phase names from frontend/database
"""

from typing import Dict, Optional


# Aliases by flow type
PHASE_ALIASES: Dict[str, Dict[str, str]] = {
    "discovery": {
        # Frontend legacy names
        "attribute_mapping": "field_mapping",
        "inventory": "asset_inventory",
        "dependencies": "dependency_analysis",  # Now redirects to Assessment
        "tech_debt": "tech_debt_assessment",  # Now redirects to Assessment
        # Database legacy names
        "data_import_validation": "data_import",
        "data_cleaning": "data_cleansing",
        "assets": "asset_inventory",
        # Special cases
        "initialization": "data_import",  # Legacy start phase
    },
    "collection": {
        "platform_detection": "asset_selection",  # Deprecated
        "automated_collection": "asset_selection",  # Deprecated
        "finalization": "synthesis",
    },
    "assessment": {
        # Legacy phase mappings to ADR-027 compliant names
        "initialization": "readiness_assessment",  # Legacy start phase
        "architecture_minimums": "readiness_assessment",
        "component_sixr_strategies": "risk_assessment",
        "app_on_page_generation": "recommendation_generation",
        # Migrated from Discovery
        "dependencies": "dependency_analysis",
        "tech_debt": "tech_debt_assessment",
        # Legacy phase names
        "tech_debt_analysis": "tech_debt_assessment",
        "finalization": "recommendation_generation",  # Legacy final phase
    },
}


def normalize_phase_name(flow_type: str, phase: str) -> str:
    """
    Normalize phase name from any variant to canonical name

    Args:
        flow_type: Flow type (discovery, collection, assessment)
        phase: Phase name (any variant)

    Returns:
        Canonical phase name

    Raises:
        ValueError: If phase invalid even after normalization
    """
    # Check if already canonical
    from app.services.flow_type_registry_helpers import get_flow_config

    try:
        config = get_flow_config(flow_type)
        canonical_names = [p.name for p in config.phases]

        if phase in canonical_names:
            return phase

        # Check aliases
        aliases = PHASE_ALIASES.get(flow_type, {})
        if phase in aliases:
            normalized = aliases[phase]

            # If alias points to phase in different flow, raise clear error
            if normalized not in canonical_names:
                raise ValueError(
                    f"Phase '{phase}' was moved from {flow_type} to another flow. "
                    f"Please use the correct flow type."
                )

            return normalized

        # Unknown phase
        raise ValueError(
            f"Unknown phase '{phase}' for flow type '{flow_type}'. "
            f"Valid phases: {canonical_names}"
        )
    except Exception as e:
        raise ValueError(f"Error normalizing phase: {e}")


def get_phase_flow_type(phase: str) -> Optional[str]:
    """
    Determine which flow type a phase belongs to

    Useful for migrated phases (dependency_analysis, tech_debt_assessment)
    that may come from legacy discovery code but now belong to assessment.

    Returns:
        Flow type string or None if phase not found
    """
    from app.services.flow_type_registry_helpers import get_all_flow_configs

    for config in get_all_flow_configs():
        phase_names = [p.name for p in config.phases]
        if phase in phase_names:
            return config.name

        # Check aliases
        aliases = PHASE_ALIASES.get(config.name, {})
        for alias, canonical in aliases.items():
            if alias == phase and canonical in phase_names:
                return config.name

    return None
