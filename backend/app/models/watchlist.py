"""
Watchlist Model - For tracking favorite stocks
"""

import uuid
from typing import Any, Dict

from sqlalchemy import Column, DateTime, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Watchlist(Base):
    """
    Watchlist model for tracking user's favorite stocks.
    """

    __tablename__ = "watchlists"
    __table_args__ = (
        UniqueConstraint(
            "client_account_id",
            "engagement_id",
            "user_id",
            "stock_symbol",
            name="uq_watchlist_user_stock",
        ),
        {"schema": "migration"},
    )

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Stock reference
    stock_symbol = Column(String(20), nullable=False, index=True)
    stock_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.stocks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Multi-tenant isolation
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)

    # Watchlist metadata
    notes = Column(String(500), nullable=True)  # User notes about this stock
    alert_price = Column(String(50), nullable=True)  # Price alert threshold

    # Timestamps
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
    stock = relationship("Stock", foreign_keys=[stock_id])

    def __repr__(self):
        return f"<Watchlist(user_id={self.user_id}, symbol={self.stock_symbol})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "stock_symbol": self.stock_symbol,
            "stock_id": str(self.stock_id) if self.stock_id else None,
            "notes": self.notes,
            "alert_price": self.alert_price,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
