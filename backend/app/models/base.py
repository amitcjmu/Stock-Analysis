"""
Base model classes for the application
"""

from datetime import datetime

from app.core.database import Base
from sqlalchemy import Column, DateTime


class TimestampMixin:
    """Mixin for adding timestamp fields to models"""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


__all__ = ["Base", "TimestampMixin"]
