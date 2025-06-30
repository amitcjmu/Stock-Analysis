"""
V3 Database Models for unified API
"""

from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Integer, Float, Enum, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum

class FlowStatus(str, enum.Enum):
    """Flow execution status"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ImportStatus(str, enum.Enum):
    """Data import status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class MappingStatus(str, enum.Enum):
    """Field mapping status"""
    SUGGESTED = "suggested"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"

class V3DataImport(Base):
    """V3 unified data import model"""
    __tablename__ = "v3_data_imports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Import metadata
    filename = Column(String, nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String)
    source_system = Column(String)
    
    # Status tracking
    status = Column(String, default="pending")
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Error tracking
    error_message = Column(String)
    error_details = Column(JSON)
    
    # Relationships
    discovery_flow = relationship("V3DiscoveryFlow", back_populates="data_import", uselist=False)
    raw_records = relationship("V3RawImportRecord", back_populates="data_import")
    field_mappings = relationship("V3FieldMapping", back_populates="data_import")
    
    # Indexes
    __table_args__ = (
        Index('idx_v3_imports_client_status', 'client_account_id', 'status'),
        Index('idx_v3_imports_created', 'created_at'),
    )

class V3DiscoveryFlow(Base):
    """V3 unified discovery flow model"""
    __tablename__ = "v3_discovery_flows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Flow identification
    flow_name = Column(String)
    flow_type = Column(String, default="unified_discovery")
    
    # Import reference
    data_import_id = Column(UUID(as_uuid=True), ForeignKey("v3_data_imports.id"))
    
    # Status tracking
    status = Column(String, default="initializing")
    current_phase = Column(String)
    phases_completed = Column(JSON, default=list)
    progress_percentage = Column(Float, default=0.0)
    
    # Flow state
    flow_state = Column(JSON, default=dict)
    crew_outputs = Column(JSON, default=dict)
    
    # Results storage
    field_mappings = Column(JSON)
    discovered_assets = Column(JSON)
    dependencies = Column(JSON)
    tech_debt_analysis = Column(JSON)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Error tracking
    error_message = Column(String)
    error_phase = Column(String)
    error_details = Column(JSON)
    
    # Relationships
    data_import = relationship("V3DataImport", back_populates="discovery_flow")
    
    # Indexes
    __table_args__ = (
        Index('idx_v3_flows_client_status', 'client_account_id', 'status'),
        Index('idx_v3_flows_import', 'data_import_id'),
    )

class V3RawImportRecord(Base):
    """V3 raw import records"""
    __tablename__ = "v3_raw_import_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_import_id = Column(UUID(as_uuid=True), ForeignKey("v3_data_imports.id"), nullable=False)
    
    # Record data
    record_index = Column(Integer, nullable=False)
    raw_data = Column(JSON, nullable=False)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    is_valid = Column(Boolean)
    validation_errors = Column(JSON)
    
    # Cleansed data
    cleansed_data = Column(JSON)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    data_import = relationship("V3DataImport", back_populates="raw_records")
    
    # Indexes
    __table_args__ = (
        Index('idx_v3_records_import', 'data_import_id'),
        Index('idx_v3_records_processed', 'is_processed'),
    )

class V3FieldMapping(Base):
    """V3 field mappings"""
    __tablename__ = "v3_field_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_import_id = Column(UUID(as_uuid=True), ForeignKey("v3_data_imports.id"), nullable=False)
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Mapping definition
    source_field = Column(String, nullable=False)
    target_field = Column(String, nullable=False)
    
    # AI suggestions
    confidence_score = Column(Float)
    match_type = Column(String)  # exact, fuzzy, semantic
    suggested_by = Column(String, default="ai_agent")
    
    # User actions
    status = Column(String, default="suggested")
    approved_by = Column(String)
    approved_at = Column(DateTime)
    
    # Transformation rules
    transformation_rules = Column(JSON)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    data_import = relationship("V3DataImport", back_populates="field_mappings")
    
    # Indexes
    __table_args__ = (
        Index('idx_v3_mappings_import', 'data_import_id'),
        Index('idx_v3_mappings_source', 'source_field'),
        Index('idx_v3_mappings_status', 'status'),
    )