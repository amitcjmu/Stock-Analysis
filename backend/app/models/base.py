"""
Base model classes for the application
"""

from datetime import datetime

from sqlalchemy import Column, DateTime

from app.core.database import Base


class TimestampMixin:
    """Mixin for adding timestamp fields to models"""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


__all__ = ["Base", "TimestampMixin"]
