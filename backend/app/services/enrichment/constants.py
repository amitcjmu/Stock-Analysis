"""
Centralized enrichment constants and mappings.

Per GPT-5 recommendation: Single source of truth for pattern type enum mappings
to avoid drift across enrichment agents.

This module provides a centralized mapping between agent pattern types and the
PostgreSQL patterntype enum values, enabling tolerant fallback and preventing
pipeline failures from enum constraint violations.
"""

from enum import Enum
from typing import Dict
import logging

logger = logging.getLogger(__name__)


# PostgreSQL enum: migration.patterntype
class PatternTypeDB(str, Enum):
    """Database-backed pattern types (PostgreSQL enum values)"""

    # Canonical pattern types (used for field mapping and general patterns)
    FIELD_MAPPING_APPROVAL = "FIELD_MAPPING_APPROVAL"
    FIELD_MAPPING_REJECTION = "FIELD_MAPPING_REJECTION"
    FIELD_MAPPING_SUGGESTION = "FIELD_MAPPING_SUGGESTION"
    TECHNOLOGY_CORRELATION = "TECHNOLOGY_CORRELATION"
    BUSINESS_VALUE_INDICATOR = "BUSINESS_VALUE_INDICATOR"
    RISK_FACTOR = "RISK_FACTOR"
    MODERNIZATION_OPPORTUNITY = "MODERNIZATION_OPPORTUNITY"
    DEPENDENCY_PATTERN = "DEPENDENCY_PATTERN"
    SECURITY_VULNERABILITY = "SECURITY_VULNERABILITY"
    PERFORMANCE_BOTTLENECK = "PERFORMANCE_BOTTLENECK"
    COMPLIANCE_REQUIREMENT = "COMPLIANCE_REQUIREMENT"

    # Agent-specific pattern types (added for enrichment agents)
    PRODUCT_MATCHING = "PRODUCT_MATCHING"
    COMPLIANCE_ANALYSIS = "COMPLIANCE_ANALYSIS"
    LICENSING_ANALYSIS = "LICENSING_ANALYSIS"
    VULNERABILITY_ANALYSIS = "VULNERABILITY_ANALYSIS"
    RESILIENCE_ANALYSIS = "RESILIENCE_ANALYSIS"
    DEPENDENCY_ANALYSIS = "DEPENDENCY_ANALYSIS"
    # Wave planning pattern types (added in migration 141)
    WAVE_PLANNING_OPTIMIZATION = "WAVE_PLANNING_OPTIMIZATION"


# Agent pattern types → PostgreSQL enum mapping
# Maps agent pattern type strings to database enum values
PATTERN_TYPE_ENUM_MAP: Dict[str, PatternTypeDB] = {
    # Direct mappings (agent type matches enum exactly)
    "product_matching": PatternTypeDB.PRODUCT_MATCHING,
    "compliance_analysis": PatternTypeDB.COMPLIANCE_ANALYSIS,
    "licensing_analysis": PatternTypeDB.LICENSING_ANALYSIS,
    "vulnerability_analysis": PatternTypeDB.VULNERABILITY_ANALYSIS,
    "resilience_analysis": PatternTypeDB.RESILIENCE_ANALYSIS,
    "dependency_analysis": PatternTypeDB.DEPENDENCY_ANALYSIS,
    # Legacy/alternative names for backward compatibility
    "product_correlation": PatternTypeDB.PRODUCT_MATCHING,
    "compliance": PatternTypeDB.COMPLIANCE_ANALYSIS,
    "licensing": PatternTypeDB.LICENSING_ANALYSIS,
    "vulnerability": PatternTypeDB.VULNERABILITY_ANALYSIS,
    "resilience": PatternTypeDB.RESILIENCE_ANALYSIS,
    "dependency": PatternTypeDB.DEPENDENCY_ANALYSIS,
    # Wave planning pattern types (migration 141)
    "wave_planning_optimization": PatternTypeDB.WAVE_PLANNING_OPTIMIZATION,
    "WAVE_PLANNING_OPTIMIZATION": PatternTypeDB.WAVE_PLANNING_OPTIMIZATION,
}

# Tolerant fallback with warning (GPT-5 recommendation)
# Used when an unknown pattern type is encountered to prevent pipeline failures
DEFAULT_PATTERN_TYPE = PatternTypeDB.TECHNOLOGY_CORRELATION


def get_db_pattern_type(agent_pattern_type: str) -> PatternTypeDB:
    """
    Map agent pattern type to database enum value.

    Uses tolerant fallback to avoid blocking pipeline on unknown types.
    Logs warning for unmapped types for monitoring and debugging.

    This function is the single source of truth for pattern type mapping
    and should be used by ALL enrichment agents when storing learnings.

    Args:
        agent_pattern_type: Pattern type from enrichment agent (e.g., "product_matching")

    Returns:
        PatternTypeDB enum value corresponding to the agent pattern type

    Examples:
        >>> get_db_pattern_type("product_matching")
        <PatternTypeDB.PRODUCT_MATCHING: 'PRODUCT_MATCHING'>

        >>> get_db_pattern_type("unknown_type")  # Falls back with warning
        <PatternTypeDB.TECHNOLOGY_CORRELATION: 'TECHNOLOGY_CORRELATION'>

    Notes:
        - Fallback ensures pipeline never blocks on unknown pattern types
        - Warning logs enable monitoring for missing mappings
        - Multi-tenant isolation maintained at caller level
    """
    if agent_pattern_type not in PATTERN_TYPE_ENUM_MAP:
        logger.warning(
            f"Unknown pattern type '{agent_pattern_type}' - using fallback "
            f"'{DEFAULT_PATTERN_TYPE.value}'. Update PATTERN_TYPE_ENUM_MAP "
            f"in app/services/enrichment/constants.py to add mapping."
        )
        return DEFAULT_PATTERN_TYPE

    return PATTERN_TYPE_ENUM_MAP[agent_pattern_type]


def validate_pattern_type_enum() -> bool:
    """
    Validate that all mapped values are valid PatternTypeDB enum members.

    This function is used in unit tests to ensure mapping integrity.

    Returns:
        True if all mappings are valid, False otherwise

    Raises:
        ValueError: If any mapped value is not a valid PatternTypeDB enum
    """
    for agent_type, db_type in PATTERN_TYPE_ENUM_MAP.items():
        if not isinstance(db_type, PatternTypeDB):
            raise ValueError(
                f"Invalid mapping for '{agent_type}': {db_type} is not a PatternTypeDB enum"
            )
        # Verify enum member exists
        if not hasattr(PatternTypeDB, db_type.name):
            raise ValueError(
                f"Invalid mapping for '{agent_type}': {db_type.name} is not a valid PatternTypeDB member"
            )

    return True
