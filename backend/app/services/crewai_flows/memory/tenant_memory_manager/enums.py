"""
Enums for multi-tenant memory management
"""

from enum import Enum


class LearningScope(Enum):
    """Learning scope levels for multi-tenant isolation"""

    DISABLED = "disabled"  # No learning persistence
    ENGAGEMENT = "engagement"  # Learning isolated to single engagement
    CLIENT = "client"  # Learning shared across client's engagements
    GLOBAL = "global"  # Learning shared across all clients (with consent)


class MemoryIsolationLevel(Enum):
    """Memory isolation levels for enterprise security"""

    STRICT = "strict"  # Complete isolation, no cross-tenant access
    MODERATE = "moderate"  # Limited sharing with explicit consent
    OPEN = "open"  # Open sharing with audit trail
