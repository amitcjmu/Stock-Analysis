"""
Base imports and configuration for RBAC models.
"""

try:
    from sqlalchemy import (
        JSON,
        UUID,
        Boolean,
        Column,
        DateTime,
        Enum,
        ForeignKey,
        Integer,
        String,
        Text,
    )
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID  # noqa: F401
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Column = String = Text = Boolean = DateTime = UUID = JSON = ForeignKey = Enum = (
        Integer
    ) = object

    def relationship(*args, **kwargs):
        return None

    class func:
        @staticmethod
        def now():
            return None


import uuid  # noqa: F401

try:
    from app.core.database import Base
except ImportError:
    Base = object
