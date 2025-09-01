"""
Collected Data Inventory Model

This model represents the collected data inventory for Collection Flows.
"""

import uuid

from sqlalchemy import UUID, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class CollectedDataInventory(Base, TimestampMixin):
    """
    Model for tracking collected data in Collection Flows.
    """

    __tablename__ = "collected_data_inventory"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    collection_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("collection_flows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    adapter_id = Column(
        UUID(as_uuid=True),
        ForeignKey("platform_adapters.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Data fields
    platform = Column(String(50), nullable=False, index=True)
    collection_method = Column(String(50), nullable=False)
    raw_data = Column(JSONB, nullable=False)
    normalized_data = Column(JSONB, nullable=True)
    data_type = Column(String(100), nullable=False, index=True)
    resource_count = Column(Integer, nullable=False, default=0, server_default="0")

    # Quality fields
    quality_score = Column(Float, nullable=True)
    validation_status = Column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )
    validation_errors = Column(JSONB, nullable=True)

    # Metadata
    inventory_metadata = Column(
        "metadata", JSONB, nullable=False, default={}, server_default="{}"
    )

    # Timestamps
    collected_at = Column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    collection_flow = relationship("CollectionFlow", back_populates="collected_data")
    adapter = relationship("PlatformAdapter", back_populates="collected_data")

    # Hybrid properties for common normalized_data fields
    # These provide direct access to JSONB fields without requiring actual columns
    @hybrid_property
    def ip_address(self):
        """Extract IP address from normalized_data JSONB field."""
        if self.normalized_data:
            return self.normalized_data.get("ip_address")
        return None

    @hybrid_property
    def server_name(self):
        """Extract server name from normalized_data JSONB field."""
        if self.normalized_data:
            return self.normalized_data.get("server_name") or self.normalized_data.get(
                "hostname"
            )
        return None

    @hybrid_property
    def os(self):
        """Extract operating system from normalized_data JSONB field."""
        if self.normalized_data:
            return (
                self.normalized_data.get("os")
                or self.normalized_data.get("operating_system")
                or self.normalized_data.get("platform")
            )
        return None

    @hybrid_property
    def hostname(self):
        """Extract hostname from normalized_data JSONB field."""
        if self.normalized_data:
            return self.normalized_data.get("hostname") or self.normalized_data.get(
                "server_name"
            )
        return None

    @hybrid_property
    def operating_system(self):
        """Extract operating system from normalized_data JSONB field (alias for os)."""
        return self.os

    def __repr__(self):
        return f"<CollectedDataInventory(id={self.id}, platform='{self.platform}', data_type='{self.data_type}')>"
