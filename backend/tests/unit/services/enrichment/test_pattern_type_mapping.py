"""
Unit tests for pattern type mapping.

Tests the centralized pattern type enum mapping module to ensure:
1. All agent pattern types map to valid database enum values
2. Unknown types use fallback with warning
3. No invalid enum values in mapping
4. Validation functions work correctly
5. Fallback doesn't block pipeline

Per Phase 0.1 of ASSESSMENT_CANONICAL_GROUPING_REMEDIATION_PLAN.md
"""

import pytest
import logging
from app.services.enrichment.constants import (
    get_db_pattern_type,
    PatternTypeDB,
    PATTERN_TYPE_ENUM_MAP,
    validate_pattern_type_enum,
    DEFAULT_PATTERN_TYPE,
)


def test_all_agent_pattern_types_mapped():
    """
    Verify all 6 agent pattern types have valid DB enum mappings.

    This test ensures that each enrichment agent's pattern type
    maps to a valid PostgreSQL enum value.
    """
    agent_types = [
        "product_matching",
        "compliance_analysis",
        "licensing_analysis",
        "vulnerability_analysis",
        "resilience_analysis",
        "dependency_analysis",
    ]

    for agent_type in agent_types:
        db_type = get_db_pattern_type(agent_type)

        # Verify returns PatternTypeDB enum
        assert isinstance(db_type, PatternTypeDB), (
            f"Agent type '{agent_type}' did not return PatternTypeDB enum, "
            f"got {type(db_type)}"
        )

        # Verify enum value exists in PatternTypeDB
        assert db_type.value in [
            e.value for e in PatternTypeDB
        ], f"Agent type '{agent_type}' mapped to invalid enum value: {db_type.value}"

        # Verify enum is a valid PostgreSQL patterntype value
        # (these match the database enum from migration)
        valid_db_values = [
            "PRODUCT_MATCHING",
            "COMPLIANCE_ANALYSIS",
            "LICENSING_ANALYSIS",
            "VULNERABILITY_ANALYSIS",
            "RESILIENCE_ANALYSIS",
            "DEPENDENCY_ANALYSIS",
        ]
        assert (
            db_type.value in valid_db_values
        ), f"Agent type '{agent_type}' mapped to unexpected value: {db_type.value}"


def test_unknown_pattern_type_uses_fallback(caplog):
    """
    Unknown pattern types should use fallback and log warning.

    This test ensures the tolerant fallback behavior works correctly:
    1. Returns DEFAULT_PATTERN_TYPE (TECHNOLOGY_CORRELATION)
    2. Logs warning with helpful message
    3. Doesn't raise exception (pipeline continues)
    """
    # Set log level to capture warnings
    caplog.set_level(logging.WARNING)

    # Test with unknown pattern type
    unknown_type = "unknown_agent_type_12345"
    result = get_db_pattern_type(unknown_type)

    # Verify fallback used
    assert (
        result == DEFAULT_PATTERN_TYPE
    ), f"Expected fallback to {DEFAULT_PATTERN_TYPE.value}, got {result.value}"
    assert (
        result == PatternTypeDB.TECHNOLOGY_CORRELATION
    ), "Fallback should be TECHNOLOGY_CORRELATION"

    # Verify warning logged
    assert (
        "Unknown pattern type" in caplog.text
    ), "Should log warning for unknown pattern type"
    assert "using fallback" in caplog.text, "Warning should mention fallback behavior"
    assert (
        unknown_type in caplog.text
    ), "Warning should include the unknown pattern type name"
    assert (
        "Update PATTERN_TYPE_ENUM_MAP" in caplog.text
    ), "Warning should include guidance for fixing"


def test_no_invalid_enum_values():
    """
    Ensure mapping only contains valid DB enum values.

    This test validates the mapping dictionary integrity:
    1. All values are PatternTypeDB enums (not strings)
    2. All enum names exist in PatternTypeDB
    3. validate_pattern_type_enum() passes
    """
    for agent_type, db_type in PATTERN_TYPE_ENUM_MAP.items():
        # Verify value is a PatternTypeDB enum instance
        assert isinstance(db_type, PatternTypeDB), (
            f"Mapping for '{agent_type}' contains non-enum value: {db_type} "
            f"(type: {type(db_type)}). Use PatternTypeDB.VALUE instead of string."
        )

        # Verify enum member exists
        assert hasattr(
            PatternTypeDB, db_type.name
        ), f"Mapping for '{agent_type}' references non-existent enum member: {db_type.name}"

        # Verify enum value matches expected format
        assert (
            db_type.value.isupper()
        ), f"Enum value for '{agent_type}' should be uppercase: {db_type.value}"
        assert db_type.value.replace(
            "_", ""
        ).isalnum(), f"Enum value for '{agent_type}' should be alphanumeric with underscores: {db_type.value}"

    # Run validation function
    assert (
        validate_pattern_type_enum() is True
    ), "validate_pattern_type_enum() should return True for valid mappings"


def test_get_db_pattern_type_returns_enum():
    """
    Verify get_db_pattern_type() always returns PatternTypeDB enum.

    This test ensures the function contract:
    1. Known types return correct enum
    2. Unknown types return fallback enum (not None, not string)
    3. Return type is always PatternTypeDB
    """
    # Test known type
    known_result = get_db_pattern_type("product_matching")
    assert isinstance(
        known_result, PatternTypeDB
    ), "Known pattern type should return PatternTypeDB enum"
    assert (
        known_result == PatternTypeDB.PRODUCT_MATCHING
    ), "product_matching should map to PRODUCT_MATCHING enum"

    # Test unknown type
    unknown_result = get_db_pattern_type("nonexistent_type")
    assert isinstance(
        unknown_result, PatternTypeDB
    ), "Unknown pattern type should still return PatternTypeDB enum (fallback)"
    assert unknown_result is not None, "Should never return None"

    # Verify return values are usable as enum values (not strings)
    assert hasattr(known_result, "value"), "Result should be enum with .value attribute"
    assert hasattr(known_result, "name"), "Result should be enum with .name attribute"


def test_fallback_doesnt_block_pipeline():
    """
    Fallback should allow pipeline to continue without raising exception.

    This test ensures resilience:
    1. Multiple unknown types don't crash
    2. Mixed known/unknown types work
    3. No exceptions raised for unknown types
    """
    # Test multiple unknown types in succession
    unknown_types = [
        "invalid_type_1",
        "invalid_type_2",
        "completely_unknown",
    ]

    for unknown_type in unknown_types:
        try:
            result = get_db_pattern_type(unknown_type)
            assert isinstance(
                result, PatternTypeDB
            ), f"Unknown type '{unknown_type}' should return PatternTypeDB enum"
            assert (
                result == DEFAULT_PATTERN_TYPE
            ), f"Unknown type '{unknown_type}' should use fallback"
        except Exception as e:
            pytest.fail(
                f"get_db_pattern_type() raised exception for unknown type '{unknown_type}': {e}. "
                f"Fallback should prevent exceptions to avoid blocking pipeline."
            )

    # Test mixed known and unknown types
    mixed_types = [
        ("product_matching", PatternTypeDB.PRODUCT_MATCHING),
        ("unknown_type", DEFAULT_PATTERN_TYPE),
        ("compliance_analysis", PatternTypeDB.COMPLIANCE_ANALYSIS),
        ("another_unknown", DEFAULT_PATTERN_TYPE),
    ]

    for pattern_type, expected_result in mixed_types:
        result = get_db_pattern_type(pattern_type)
        assert (
            result == expected_result
        ), f"Mixed type '{pattern_type}' should map to {expected_result.value}, got {result.value}"


def test_backward_compatibility_mappings():
    """
    Verify legacy/alternative pattern type names map correctly.

    This test ensures backward compatibility for agents that may use
    alternative naming conventions.
    """
    legacy_mappings = [
        ("product_correlation", PatternTypeDB.PRODUCT_MATCHING),
        ("compliance", PatternTypeDB.COMPLIANCE_ANALYSIS),
        ("licensing", PatternTypeDB.LICENSING_ANALYSIS),
        ("vulnerability", PatternTypeDB.VULNERABILITY_ANALYSIS),
        ("resilience", PatternTypeDB.RESILIENCE_ANALYSIS),
        ("dependency", PatternTypeDB.DEPENDENCY_ANALYSIS),
    ]

    for legacy_name, expected_enum in legacy_mappings:
        result = get_db_pattern_type(legacy_name)
        assert (
            result == expected_enum
        ), f"Legacy name '{legacy_name}' should map to {expected_enum.value}, got {result.value}"


def test_canonical_pattern_types_available():
    """
    Verify canonical pattern types are available in enum.

    These are used by other parts of the system (field mapping, etc.)
    and should remain available even if not used by enrichment agents.
    """
    canonical_types = [
        PatternTypeDB.FIELD_MAPPING_APPROVAL,
        PatternTypeDB.FIELD_MAPPING_REJECTION,
        PatternTypeDB.FIELD_MAPPING_SUGGESTION,
        PatternTypeDB.TECHNOLOGY_CORRELATION,
        PatternTypeDB.BUSINESS_VALUE_INDICATOR,
        PatternTypeDB.RISK_FACTOR,
        PatternTypeDB.MODERNIZATION_OPPORTUNITY,
        PatternTypeDB.DEPENDENCY_PATTERN,
        PatternTypeDB.SECURITY_VULNERABILITY,
        PatternTypeDB.PERFORMANCE_BOTTLENECK,
        PatternTypeDB.COMPLIANCE_REQUIREMENT,
    ]

    for canonical_type in canonical_types:
        # Verify enum exists
        assert isinstance(
            canonical_type, PatternTypeDB
        ), f"Canonical type {canonical_type} should be PatternTypeDB enum"

        # Verify enum value exists in PatternTypeDB
        assert canonical_type in list(
            PatternTypeDB
        ), f"Canonical type {canonical_type} should be in PatternTypeDB enum"
