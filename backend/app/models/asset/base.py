"""
Base classes and imports for asset models.

This module contains the core imports, base classes, and utility
functions used across all asset model modules.
"""

try:
    from sqlalchemy import (
        JSON,
        Boolean,
        CheckConstraint,
        Column,
        DateTime,
        Enum,
        Float,
        ForeignKey,
        Integer,
        String,
        Text,
    )
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Column = Integer = String = DateTime = Text = JSON = Enum = Boolean = ForeignKey = (
        Float
    ) = PostgresUUID = CheckConstraint = object

    def relationship(*args, **kwargs):
        return None

    class func:
        @staticmethod
        def now():
            return None


try:
    from app.core.database import Base
except ImportError:
    Base = object

try:
    import uuid
except ImportError:

    class uuid:
        @staticmethod
        def uuid4():
            return None


# Common field lengths
SMALL_STRING_LENGTH = 50
MEDIUM_STRING_LENGTH = 100
LARGE_STRING_LENGTH = 255
IP_ADDRESS_LENGTH = 45  # Supports IPv6
MAC_ADDRESS_LENGTH = 17

# Default values
DEFAULT_MIGRATION_PRIORITY = 5
DEFAULT_STATUS = "active"
DEFAULT_MIGRATION_STATUS = "discovered"
DEFAULT_ASSESSMENT_READINESS = "not_ready"
DEFAULT_CURRENT_PHASE = "discovery"
DEFAULT_SOURCE_PHASE = "discovery"

# Scoring constants
MIN_SCORE = 0.0
MAX_SCORE = 100.0
DEFAULT_SCORE = 50.0

# Complexity penalties for migration readiness
COMPLEXITY_PENALTIES = {"high": 30, "medium": 15, "low": 5}

# Asset type priority mapping
ASSET_TYPE_PRIORITIES = {
    "database": 1,  # Highest priority
    "application": 2,
    "server": 3,
    "component": 4,
    "network": 5,
    "storage": 6,
    "security_group": 7,
    "load_balancer": 8,
    "virtual_machine": 9,
    "container": 10,
    "other": 11,  # Lowest priority
}
