"""
Discovery Asset Database Model
Normalized asset storage from Discovery Flow results.
Follows the Multi-Flow Architecture Implementation Plan.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Float, Boolean, UUID as SQLAlchemyUUID, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class DiscoveryAsset(Base):
    """
    Discovery assets - normalized
    Created automatically from Discovery Flow results
    """
    __tablename__ = "discovery_assets"
    
    # Primary key
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to discovery flow
    discovery_flow_id = Column(SQLAlchemyUUID(as_uuid=True), 
                              ForeignKey('discovery_flows.id'), 
                              nullable=False, index=True)
    
    # Multi-tenant isolation (inherited from discovery flow)
    client_account_id = Column(SQLAlchemyUUID(as_uuid=True), 
                              default=uuid.UUID("11111111-1111-1111-1111-111111111111"), 
                              nullable=False, index=True)
    engagement_id = Column(SQLAlchemyUUID(as_uuid=True), 
                          default=uuid.UUID("22222222-2222-2222-2222-222222222222"), 
                          nullable=False, index=True)
    
    # Asset identification
    asset_name = Column(String(255), nullable=False, index=True)
    asset_type = Column(String(100), nullable=False, index=True)  # server, database, application, device, etc.
    asset_subtype = Column(String(100), index=True)  # web_server, database_server, mobile_app, etc.
    
    # Asset data - comprehensive storage
    asset_data = Column(JSON, nullable=False)  # All asset attributes from discovery
    original_source_data = Column(JSON)  # Original CMDB data before processing
    
    # Discovery phase tracking
    discovered_in_phase = Column(String(50), nullable=False, index=True)  # which phase discovered this asset
    discovery_method = Column(String(100))  # how asset was discovered (crew, agent, etc.)
    
    # Quality and validation
    quality_score = Column(Float, default=0.0)  # Asset data quality score
    validation_status = Column(String(20), default="pending", nullable=False)  # pending, validated, failed
    validation_results = Column(JSON, default=dict)  # Detailed validation results
    confidence_score = Column(Float, default=0.0)  # Classification confidence
    
    # Agent insights
    agent_classification = Column(JSON, default=dict)  # Agent classification results
    agent_insights = Column(JSON, default=list)  # Agent-generated insights about this asset
    crew_analysis = Column(JSON, default=dict)  # Crew-level analysis results
    
    # Relationships and dependencies
    hosting_relationships = Column(JSON, default=list)  # What this asset hosts
    hosted_by_relationships = Column(JSON, default=list)  # What hosts this asset
    application_dependencies = Column(JSON, default=list)  # App-to-app dependencies
    
    # Technical debt and modernization
    tech_debt_score = Column(Float, default=0.0)  # Technical debt assessment
    modernization_priority = Column(String(20))  # high, medium, low
    six_r_recommendation = Column(String(50))  # rehost, replatform, refactor, etc.
    modernization_complexity = Column(String(20))  # simple, moderate, complex
    
    # Migration readiness
    migration_ready = Column(Boolean, default=False, nullable=False)
    migration_blockers = Column(JSON, default=list)  # List of migration blockers
    migration_dependencies = Column(JSON, default=list)  # Migration dependencies
    
    # Enterprise features
    learning_tags = Column(JSON, default=list)  # Tags for learning system
    knowledge_base_matches = Column(JSON, default=list)  # Matched knowledge base entries
    
    # Asset lifecycle
    asset_status = Column(String(20), default="active", nullable=False)  # active, deprecated, retired
    last_updated_in_source = Column(DateTime(timezone=True))  # When asset was last updated in source system
    
    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    discovery_flow = relationship("DiscoveryFlow", back_populates="assets")
    
    def __repr__(self):
        return f"<DiscoveryAsset(name='{self.asset_name}', type='{self.asset_type}', phase='{self.discovered_in_phase}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "discovery_flow_id": str(self.discovery_flow_id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "asset_name": self.asset_name,
            "asset_type": self.asset_type,
            "asset_subtype": self.asset_subtype,
            "asset_data": self.asset_data or {},
            "discovered_in_phase": self.discovered_in_phase,
            "discovery_method": self.discovery_method,
            "quality_score": self.quality_score,
            "validation_status": self.validation_status,
            "validation_results": self.validation_results or {},
            "confidence_score": self.confidence_score,
            "agent_classification": self.agent_classification or {},
            "agent_insights": self.agent_insights or [],
            "crew_analysis": self.crew_analysis or {},
            "hosting_relationships": self.hosting_relationships or [],
            "hosted_by_relationships": self.hosted_by_relationships or [],
            "application_dependencies": self.application_dependencies or [],
            "tech_debt_score": self.tech_debt_score,
            "modernization_priority": self.modernization_priority,
            "six_r_recommendation": self.six_r_recommendation,
            "modernization_complexity": self.modernization_complexity,
            "migration_ready": self.migration_ready,
            "migration_blockers": self.migration_blockers or [],
            "migration_dependencies": self.migration_dependencies or [],
            "learning_tags": self.learning_tags or [],
            "knowledge_base_matches": self.knowledge_base_matches or [],
            "asset_status": self.asset_status,
            "last_updated_in_source": self.last_updated_in_source.isoformat() if self.last_updated_in_source else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_summary(self):
        """Get a summary of the asset for dashboards"""
        return {
            "id": str(self.id),
            "name": self.asset_name,
            "type": self.asset_type,
            "subtype": self.asset_subtype,
            "quality_score": self.quality_score,
            "confidence_score": self.confidence_score,
            "validation_status": self.validation_status,
            "tech_debt_score": self.tech_debt_score,
            "six_r_recommendation": self.six_r_recommendation,
            "migration_ready": self.migration_ready,
            "discovered_in_phase": self.discovered_in_phase
        } 