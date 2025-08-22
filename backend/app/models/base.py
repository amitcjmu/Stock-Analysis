"""
Base model classes for the application
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime

from app.core.database import Base


class TimestampMixin:
    """Mixin for adding timestamp fields to models"""

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


__all__ = ["Base", "TimestampMixin"]
