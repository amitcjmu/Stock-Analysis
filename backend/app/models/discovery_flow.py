"""
Discovery Flow Database Model
Fresh architecture for Discovery Flow with CrewAI Flow ID as single source of truth.
Follows the Multi-Flow Architecture Implementation Plan.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Float, Boolean, UUID as SQLAlchemyUUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class DiscoveryFlow(Base):
    """
    Master flow entity - Discovery focused
    Uses CrewAI Flow ID as single source of truth (no session_id confusion)
    """
    __tablename__ = "discovery_flows"
    
    # Primary key - CrewAI Flow ID as single source of truth
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_id = Column(String(255), unique=True, nullable=False, index=True)  # CrewAI generated flow ID
    
    # Multi-tenant isolation (reuse demo constants)
    client_account_id = Column(SQLAlchemyUUID(as_uuid=True), 
                              default=uuid.UUID("11111111-1111-1111-1111-111111111111"), 
                              nullable=False, index=True)  # Demo Client
    engagement_id = Column(SQLAlchemyUUID(as_uuid=True), 
                          default=uuid.UUID("22222222-2222-2222-2222-222222222222"), 
                          nullable=False, index=True)     # Demo Engagement
    user_id = Column(SQLAlchemyUUID(as_uuid=True), 
                     default=uuid.UUID("33333333-3333-3333-3333-333333333333"), 
                     nullable=False, index=True)          # Demo User
    
    # Discovery flow state
    current_phase = Column(String(100), default="data_import", nullable=False)
    progress_percentage = Column(Float, default=0.0, nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active, completed, failed, paused
    
    # CrewAI integration
    crewai_flow_state = Column(JSON)  # Native CrewAI flow state
    crewai_persistence_id = Column(String(255), index=True)  # CrewAI @persist() reference
    
    # Import connection
    import_session_id = Column(SQLAlchemyUUID(as_uuid=True), index=True)  # Links to import data
    
    # Discovery results - comprehensive phase data
    raw_data = Column(JSON)              # Imported raw data
    field_mappings = Column(JSON)        # Attribute mapping results
    cleaned_data = Column(JSON)          # Data cleansing results
    asset_inventory = Column(JSON)       # Discovered assets
    dependencies = Column(JSON)          # Dependency analysis
    tech_debt = Column(JSON)             # Tech debt analysis
    
    # Phase completion tracking
    data_import_completed = Column(Boolean, default=False, nullable=False)
    attribute_mapping_completed = Column(Boolean, default=False, nullable=False)
    data_cleansing_completed = Column(Boolean, default=False, nullable=False)
    inventory_completed = Column(Boolean, default=False, nullable=False)
    dependencies_completed = Column(Boolean, default=False, nullable=False)
    tech_debt_completed = Column(Boolean, default=False, nullable=False)
    
    # CrewAI crew coordination data
    crew_status = Column(JSON, default=dict)  # Manager and agent coordination
    agent_insights = Column(JSON, default=list)  # Agent collaboration results
    crew_performance_metrics = Column(JSON, default=dict)  # Performance tracking
    
    # Enterprise features
    learning_scope = Column(String(50), default="engagement", nullable=False)
    memory_isolation_level = Column(String(20), default="strict", nullable=False)
    shared_memory_refs = Column(JSON, default=list)  # Agent memory references
    knowledge_base_refs = Column(JSON, default=list)  # Knowledge base references
    
    # Error handling and logging
    errors = Column(JSON, default=list)
    warnings = Column(JSON, default=list)
    workflow_log = Column(JSON, default=list)
    
    # Assessment handoff preparation
    assessment_ready = Column(Boolean, default=False, nullable=False)
    assessment_package = Column(JSON)  # Prepared data for Assessment Flow
    
    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    assets = relationship("DiscoveryAsset", back_populates="discovery_flow", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DiscoveryFlow(flow_id='{self.flow_id}', phase='{self.current_phase}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "flow_id": self.flow_id,
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "user_id": str(self.user_id),
            "current_phase": self.current_phase,
            "progress_percentage": self.progress_percentage,
            "status": self.status,
            "phase_completion": {
                "data_import": self.data_import_completed,
                "attribute_mapping": self.attribute_mapping_completed,
                "data_cleansing": self.data_cleansing_completed,
                "inventory": self.inventory_completed,
                "dependencies": self.dependencies_completed,
                "tech_debt": self.tech_debt_completed
            },
            "raw_data": self.raw_data or [],
            "field_mappings": self.field_mappings or {},
            "cleaned_data": self.cleaned_data or {},
            "asset_inventory": self.asset_inventory or {},
            "dependencies": self.dependencies or {},
            "tech_debt": self.tech_debt or {},
            "crew_status": self.crew_status or {},
            "agent_insights": self.agent_insights or [],
            "errors": self.errors or [],
            "warnings": self.warnings or [],
            "assessment_ready": self.assessment_ready,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        } 