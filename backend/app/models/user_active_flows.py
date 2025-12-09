"""
User Active Flows Model

This model tracks which flows are currently active for each user,
supporting the session-to-flow refactor by enabling proper user
flow context management.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class UserActiveFlow(Base):
    """
    Tracks which flows are currently active for each user.

    This table enables:
    - User flow context management
    - Flow switching functionality
    - Multi-flow tracking per user
    - Current flow designation
    """

    __tablename__ = "user_active_flows"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    flow_id = Column(
        UUID(as_uuid=True), nullable=False, index=True
    )  # References any flow table
    engagement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Flow state
    activated_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_current = Column(Boolean, default=False, nullable=False, index=True)

    # Audit fields
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="active_flows")
    engagement = relationship("Engagement", back_populates="user_active_flows")

    # Table constraints
    __table_args__ = (
        # Unique constraint: each user can have each flow active only once
        UniqueConstraint("user_id", "flow_id", name="uq_user_active_flows_user_flow"),
        # Note: CHECK constraint with subquery is not supported in PostgreSQL
        # The constraint to ensure only one current flow per user per engagement
        # is enforced at the application level in the class methods
    )

    def __repr__(self):
        return f"<UserActiveFlow(user_id={self.user_id}, flow_id={self.flow_id}, is_current={self.is_current})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "flow_id": str(self.flow_id),
            "engagement_id": str(self.engagement_id),
            "activated_at": self.activated_at.isoformat(),
            "is_current": self.is_current,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def get_user_current_flow(
        cls, db, user_id: uuid.UUID, engagement_id: uuid.UUID
    ) -> Optional["UserActiveFlow"]:
        """Get the current active flow for a user in an engagement"""
        return (
            db.query(cls)
            .filter(
                cls.user_id == user_id,
                cls.engagement_id == engagement_id,
                cls.is_current == True,  # noqa: E712
            )
            .first()
        )

    @classmethod
    def get_user_active_flows(
        cls, db, user_id: uuid.UUID, engagement_id: uuid.UUID
    ) -> List["UserActiveFlow"]:
        """Get all active flows for a user in an engagement"""
        return (
            db.query(cls)
            .filter(cls.user_id == user_id, cls.engagement_id == engagement_id)
            .order_by(cls.activated_at.desc())
            .all()
        )

    @classmethod
    def set_current_flow(
        cls, db, user_id: uuid.UUID, engagement_id: uuid.UUID, flow_id: uuid.UUID
    ):
        """Set a flow as current for a user (clears other current flows)"""
        # Clear all current flows for this user in this engagement
        db.query(cls).filter(
            cls.user_id == user_id,
            cls.engagement_id == engagement_id,
            cls.is_current == True,  # noqa: E712
        ).update({"is_current": False})

        # Set the specified flow as current
        active_flow = (
            db.query(cls)
            .filter(
                cls.user_id == user_id,
                cls.engagement_id == engagement_id,
                cls.flow_id == flow_id,
            )
            .first()
        )

        if active_flow:
            active_flow.is_current = True
            active_flow.updated_at = datetime.utcnow()
        else:
            # Create new active flow record
            active_flow = cls(
                user_id=user_id,
                engagement_id=engagement_id,
                flow_id=flow_id,
                is_current=True,
                activated_at=datetime.utcnow(),
            )
            db.add(active_flow)

        db.commit()
        return active_flow

    @classmethod
    def activate_flow(
        cls,
        db,
        user_id: uuid.UUID,
        engagement_id: uuid.UUID,
        flow_id: uuid.UUID,
        set_as_current: bool = True,
    ):
        """Activate a flow for a user"""
        # Check if flow is already active
        existing = (
            db.query(cls)
            .filter(
                cls.user_id == user_id,
                cls.engagement_id == engagement_id,
                cls.flow_id == flow_id,
            )
            .first()
        )

        if existing:
            if set_as_current:
                return cls.set_current_flow(db, user_id, engagement_id, flow_id)
            return existing

        # Create new active flow
        active_flow = cls(
            user_id=user_id,
            engagement_id=engagement_id,
            flow_id=flow_id,
            is_current=set_as_current,
            activated_at=datetime.utcnow(),
        )

        if set_as_current:
            # Clear other current flows first
            db.query(cls).filter(
                cls.user_id == user_id,
                cls.engagement_id == engagement_id,
                cls.is_current == True,  # noqa: E712
            ).update({"is_current": False})

        db.add(active_flow)
        db.commit()
        return active_flow

    @classmethod
    def deactivate_flow(
        cls, db, user_id: uuid.UUID, engagement_id: uuid.UUID, flow_id: uuid.UUID
    ):
        """Deactivate a flow for a user"""
        active_flow = (
            db.query(cls)
            .filter(
                cls.user_id == user_id,
                cls.engagement_id == engagement_id,
                cls.flow_id == flow_id,
            )
            .first()
        )

        if active_flow:
            db.delete(active_flow)
            db.commit()
            return True
        return False
