"""
Discovery Asset Model - Phase 3: Database Integration
Normalized asset storage eliminating session_id dependencies
"""
import uuid
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class DiscoveryAsset(Base):
    """
    Normalized asset storage for discovery flow results.
    CrewAI Flow ID based architecture, eliminating session_id dependencies.
    """
    __tablename__ = 'discovery_assets'

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Flow relationship - CrewAI Flow ID based
    discovery_flow_id = Column(UUID(as_uuid=True), ForeignKey('discovery_flows.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Multi-tenant isolation
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Asset identification
    asset_name = Column(String(255), nullable=False)
    asset_type = Column(String(100), nullable=True, index=True)
    asset_subtype = Column(String(100), nullable=True)
    
    # Asset data
    raw_data = Column(JSONB, nullable=False)
    normalized_data = Column(JSONB, nullable=True)
    
    # Discovery metadata
    discovered_in_phase = Column(String(50), nullable=False)
    discovery_method = Column(String(100), nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Migration assessment
    migration_ready = Column(Boolean, nullable=False, default=False)
    migration_complexity = Column(String(20), nullable=True)  # low, medium, high, critical
    migration_priority = Column(Integer, nullable=True)
    
    # Status tracking
    asset_status = Column(String(20), nullable=False, default='discovered', index=True)
    validation_status = Column(String(20), nullable=False, default='pending')
    
    # Demo mode support
    is_mock = Column(Boolean, nullable=False, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    discovery_flow = relationship("DiscoveryFlow", back_populates="assets")

    def __repr__(self):
        return f"<DiscoveryAsset(name='{self.asset_name}', type='{self.asset_type}', status='{self.asset_status}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "discovery_flow_id": str(self.discovery_flow_id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "asset_name": self.asset_name,
            "asset_type": self.asset_type,
            "asset_subtype": self.asset_subtype,
            "raw_data": self.raw_data,
            "normalized_data": self.normalized_data,
            "discovered_in_phase": self.discovered_in_phase,
            "discovery_method": self.discovery_method,
            "confidence_score": self.confidence_score,
            "migration_ready": self.migration_ready,
            "migration_complexity": self.migration_complexity,
            "migration_priority": self.migration_priority,
            "asset_status": self.asset_status,
            "validation_status": self.validation_status,
            "is_mock": self.is_mock,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def to_asset_model(self) -> Dict[str, Any]:
        """Convert to legacy Asset model format for backward compatibility"""
        return {
            "id": str(self.id),
            "name": self.asset_name,
            "type": self.asset_type,
            "subtype": self.asset_subtype,
            "status": self.asset_status,
            "migration_ready": self.migration_ready,
            "migration_complexity": self.migration_complexity,
            "migration_priority": self.migration_priority,
            "raw_data": self.raw_data,
            "normalized_data": self.normalized_data,
            "metadata": {
                "discovered_in_phase": self.discovered_in_phase,
                "discovery_method": self.discovery_method,
                "confidence_score": self.confidence_score,
                "validation_status": self.validation_status,
                "client_account_id": str(self.client_account_id),
                "engagement_id": str(self.engagement_id),
                "discovery_flow_id": str(self.discovery_flow_id)
            }
        }

    def update_migration_assessment(self, ready: bool, complexity: str = None, priority: int = None):
        """Update migration assessment fields"""
        self.migration_ready = ready
        if complexity:
            self.migration_complexity = complexity
        if priority:
            self.migration_priority = priority
        self.asset_status = 'assessed' if ready else 'needs_review' 