"""
Base schema definitions for migration field schema.

Contains enums and foundational types used across all field definitions.
"""

from enum import Enum


class FieldCategory(str, Enum):
    """Field categories for organizing questionnaire sections."""

    IDENTITY = "identity"
    BUSINESS = "business"
    TECHNICAL = "technical"
    INFRASTRUCTURE = "infrastructure"
    DEPENDENCIES = "dependencies"
    COMPLIANCE = "compliance"
    MIGRATION = "migration"
    OPERATIONS = "operations"


class FieldPriority(str, Enum):
    """Field priority levels for gap analysis."""

    CRITICAL = "critical"  # Must have for migration planning
    HIGH = "high"  # Important for accurate assessment
    MEDIUM = "medium"  # Useful for optimization
    LOW = "low"  # Nice to have
