"""
Comprehensive Migration Field Schema - 6R Assessment Aligned

Defines ALL fields required for accurate 6R strategy recommendation:
- Rehost: Lift-and-shift to cloud (needs infrastructure specs)
- Replatform: Minor optimizations (needs tech stack compatibility)
- Refactor: Re-architect for cloud (needs architecture patterns, code base)
- Repurchase: Replace with SaaS (needs business process, vendor alternatives)
- Retire: Decommission (needs usage data, business justification)
- Retain: Keep as-is (needs compliance requirements, constraints)

This schema ensures gap analysis identifies EVERY missing field needed for
proper 6R assessment, not just basic inventory data.

Public API:
    Enums:
        - FieldCategory: Field categories for organizing sections
        - FieldPriority: Field priority levels for gap analysis

    Field Constants:
        - CORE_FIELDS: Fields applicable to all asset types
        - APPLICATION_FIELDS: Application-specific fields
        - DATABASE_FIELDS: Database-specific fields
        - SERVER_FIELDS: Server-specific fields

    Field Retrieval:
        - get_fields_for_asset_type: Get all fields for a specific asset type
        - get_fields_by_category: Organize fields by category
        - get_critical_fields: Get critical priority fields
        - get_high_priority_fields: Get high priority fields

    6R Assessment:
        - get_six_r_decision_fields: Get fields organized by 6R strategy
        - validate_assessment_readiness: Validate asset readiness for 6R assessment

    Legacy Support:
        - MigrationFieldSchema: Class-based interface (maintains backward compatibility)
"""

# Base schemas
from .base_schemas import FieldCategory, FieldPriority

# Field definitions
from .field_definitions import (
    CORE_FIELDS,
    APPLICATION_FIELDS,
    DATABASE_FIELDS,
    SERVER_FIELDS,
    get_fields_for_asset_type,
)

# Response helpers
from .response_schemas import (
    get_fields_by_category,
    get_critical_fields,
    get_high_priority_fields,
)

# Validation functions
from .validation_schemas import (
    get_six_r_decision_fields,
    validate_assessment_readiness,
)


class MigrationFieldSchema:
    """
    Legacy class-based interface for migration field schema.

    This class maintains backward compatibility with code that uses the
    class-based interface. New code should use the module-level functions
    directly for better clarity and testability.
    """

    # Expose field constants as class attributes
    CORE_FIELDS = CORE_FIELDS
    APPLICATION_FIELDS = APPLICATION_FIELDS
    DATABASE_FIELDS = DATABASE_FIELDS
    SERVER_FIELDS = SERVER_FIELDS

    @classmethod
    def get_fields_for_asset_type(cls, asset_type: str):
        """Get all applicable fields for a given asset type."""
        return get_fields_for_asset_type(asset_type)

    @classmethod
    def get_fields_by_category(cls, asset_type: str = None):
        """Get fields organized by category."""
        return get_fields_by_category(asset_type)

    @classmethod
    def get_critical_fields(cls, asset_type: str = None):
        """Get all CRITICAL priority fields for an asset type."""
        return get_critical_fields(asset_type)

    @classmethod
    def get_high_priority_fields(cls, asset_type: str = None):
        """Get all HIGH priority fields for an asset type."""
        return get_high_priority_fields(asset_type)

    @classmethod
    def get_six_r_decision_fields(cls, asset_type: str = None):
        """Get fields organized by which 6R strategy they inform."""
        return get_six_r_decision_fields(asset_type)

    @classmethod
    def validate_assessment_readiness(cls, asset, asset_type: str = None):
        """Validate if asset has sufficient data for 6R assessment."""
        return validate_assessment_readiness(asset, asset_type)


# Define public API exports
__all__ = [
    # Enums
    "FieldCategory",
    "FieldPriority",
    # Field constants
    "CORE_FIELDS",
    "APPLICATION_FIELDS",
    "DATABASE_FIELDS",
    "SERVER_FIELDS",
    # Field retrieval functions
    "get_fields_for_asset_type",
    "get_fields_by_category",
    "get_critical_fields",
    "get_high_priority_fields",
    # 6R assessment functions
    "get_six_r_decision_fields",
    "validate_assessment_readiness",
    # Legacy class interface
    "MigrationFieldSchema",
]
