"""
Base imports and enums for 6R Analysis models.
"""

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
    from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    # Create dummy classes for type hints
    Column = Integer = String = DateTime = Text = JSON = Enum = Boolean = ForeignKey = (
        Float
    ) = object

    def relationship(*args, **kwargs):
        return None

    class func:
        @staticmethod
        def now():
            return None


import enum
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from app.core.database import Base
    from app.models.asset import SixRStrategy
    from app.schemas.sixr_analysis import AnalysisStatus, ApplicationType, QuestionType
except ImportError:
    Base = object

    # Define enums locally if schemas not available

    class AnalysisStatus(str, enum.Enum):
        PENDING = "pending"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        FAILED = "failed"
        REQUIRES_INPUT = "requires_input"

    class QuestionType(str, enum.Enum):
        TEXT = "text"
        SELECT = "select"
        MULTISELECT = "multiselect"
        FILE_UPLOAD = "file_upload"
        BOOLEAN = "boolean"
        NUMERIC = "numeric"

    class ApplicationType(str, enum.Enum):
        CUSTOM = "custom"
        COTS = "cots"
        HYBRID = "hybrid"


# Export all for convenience
__all__ = [
    "Base",
    "Column",
    "DateTime",
    "Enum",
    "Float",
    "ForeignKey",
    "Integer",
    "String",
    "Text",
    "JSON",
    "JSONB",
    "Boolean",
    "PostgresUUID",
    "relationship",
    "func",
    "uuid",
    "datetime",
    "Any",
    "Dict",
    "List",
    "Optional",
    "SixRStrategy",
    "AnalysisStatus",
    "ApplicationType",
    "QuestionType",
    "SQLALCHEMY_AVAILABLE",
]
