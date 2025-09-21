"""
SQLAlchemy models for maintenance windows and blackout periods.

This module defines models for tracking scheduled maintenance windows
and blackout periods at various scopes (tenant, application, asset).
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class MaintenanceWindows(Base, TimestampMixin):
    """
    Scheduled maintenance windows.

    This table tracks maintenance windows at different scopes including
    tenant-wide, application-specific, or asset-specific windows.
    """

    __tablename__ = "maintenance_windows"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenant scoping
    client_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engagement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Scope specification
    scope_type = Column(String(20), nullable=False)  # tenant, application, asset
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.canonical_applications.id", ondelete="CASCADE"),
        nullable=True,
    )
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Window details
    name = Column(String(255), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    recurring = Column(Boolean, nullable=False, default=False)
    timezone = Column(String(50), nullable=True)  # Timezone identifier

    # Relationships
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")
    application = relationship("CanonicalApplication")
    asset = relationship("Asset")

    def __repr__(self):
        return f"<MaintenanceWindows(id={self.id}, name='{self.name}', scope='{self.scope_type}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "scope_type": self.scope_type,
            "application_id": str(self.application_id) if self.application_id else None,
            "asset_id": str(self.asset_id) if self.asset_id else None,
            "name": self.name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "recurring": self.recurring,
            "timezone": self.timezone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_active(self, check_time: Optional[datetime] = None) -> bool:
        """Check if maintenance window is currently active."""
        if not check_time:
            check_time = datetime.utcnow()

        return self.start_time <= check_time <= self.end_time

    def conflicts_with(self, other_start: datetime, other_end: datetime) -> bool:
        """Check if this maintenance window conflicts with another time period."""
        return not (other_end <= self.start_time or other_start >= self.end_time)


class BlackoutPeriods(Base, TimestampMixin):
    """
    Blackout periods for migrations.

    This table tracks periods when migrations or changes are not allowed
    at various scopes (tenant, application, asset).
    """

    __tablename__ = "blackout_periods"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenant scoping
    client_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engagement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Scope specification
    scope_type = Column(String(20), nullable=False)  # tenant, application, asset
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.canonical_applications.id", ondelete="CASCADE"),
        nullable=True,
    )
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Blackout period details
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)  # Reason for blackout

    # Relationships
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")
    application = relationship("CanonicalApplication")
    asset = relationship("Asset")

    def __repr__(self):
        return f"<BlackoutPeriods(id={self.id}, scope='{self.scope_type}', start={self.start_date}, end={self.end_date})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "scope_type": self.scope_type,
            "application_id": str(self.application_id) if self.application_id else None,
            "asset_id": str(self.asset_id) if self.asset_id else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_active(self, check_date: Optional[datetime] = None) -> bool:
        """Check if blackout period is currently active."""
        if not check_date:
            check_date = datetime.utcnow().date()
        elif isinstance(check_date, datetime):
            check_date = check_date.date()

        return self.start_date <= check_date <= self.end_date

    def conflicts_with(self, other_start: datetime, other_end: datetime) -> bool:
        """Check if this blackout period conflicts with another time period."""
        # Convert datetime to date for comparison
        if isinstance(other_start, datetime):
            other_start = other_start.date()
        if isinstance(other_end, datetime):
            other_end = other_end.date()

        return not (other_end < self.start_date or other_start > self.end_date)
