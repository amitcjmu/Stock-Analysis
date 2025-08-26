"""
Common imports and utilities for client account models.
"""

import uuid

try:
    from sqlalchemy import (
        JSON,
        UUID,
        Boolean,
        Column,
        DateTime,
        ForeignKey,
        Integer,
        String,
        Text,
        UniqueConstraint,
    )
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
    from sqlalchemy.ext.associationproxy import association_proxy
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Column = String = Text = Boolean = DateTime = UUID = JSON = ForeignKey = object

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

__all__ = [
    "uuid",
    "JSON",
    "UUID",
    "Boolean",
    "Column",
    "DateTime",
    "ForeignKey",
    "Integer",
    "String",
    "Text",
    "UniqueConstraint",
    "PostgresUUID",
    "association_proxy",
    "relationship",
    "func",
    "Base",
    "SQLALCHEMY_AVAILABLE",
]
