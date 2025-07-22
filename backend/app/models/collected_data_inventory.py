"""
Collected Data Inventory Model

This model represents the collected data inventory for Collection Flows.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import UUID, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
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
    collection_flow_id = Column(UUID(as_uuid=True), ForeignKey("collection_flows.id", ondelete="CASCADE"), nullable=False, index=True)
    adapter_id = Column(UUID(as_uuid=True), ForeignKey("platform_adapters.id", ondelete="SET NULL"), nullable=True)
    
    # Data fields
    platform = Column(String(50), nullable=False, index=True)
    collection_method = Column(String(50), nullable=False)
    raw_data = Column(JSONB, nullable=False)
    normalized_data = Column(JSONB, nullable=True)
    data_type = Column(String(100), nullable=False, index=True)
    resource_count = Column(Integer, nullable=False, default=0, server_default="0")
    
    # Quality fields
    quality_score = Column(Float, nullable=True)
    validation_status = Column(String(20), nullable=False, default="pending", server_default="pending", index=True)
    validation_errors = Column(JSONB, nullable=True)
    
    # Metadata
    inventory_metadata = Column("metadata", JSONB, nullable=False, default={}, server_default="{}")
    
    # Timestamps
    collected_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    collection_flow = relationship("CollectionFlow", back_populates="collected_data")
    adapter = relationship("PlatformAdapter", back_populates="collected_data")
    
    def __repr__(self):
        return f"<CollectedDataInventory(id={self.id}, platform='{self.platform}', data_type='{self.data_type}')>"