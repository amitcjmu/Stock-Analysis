"""
Base classes and imports for asset models.

This module contains the core imports, base classes, and utility
functions used across all asset model modules.
"""

import uuid

try:
    from sqlalchemy import (
        JSON,
        Boolean,
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
    ) = object

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
    "network": 4,
    "storage": 5,
    "security_group": 6,
    "load_balancer": 7,
    "virtual_machine": 8,
    "container": 9,
    "other": 10,  # Lowest priority
}
