"""
Core Data Import Models
"""
import uuid as uuid_pkg
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    JSON,
    Boolean,
    ForeignKey,
    Float,
    UUID,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from app.core.database import Base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()

class DataImport(Base):
    """
    Model for tracking data import jobs and their metadata.
    Enhanced for multi-tenancy and session management.
    """

    __tablename__ = "data_imports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    client_account_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id", ondelete="CASCADE"), nullable=True)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=True)
    master_flow_id = Column(UUID(as_uuid=True), ForeignKey("crewai_flow_state_extensions.id", ondelete="CASCADE"), nullable=True)

    import_name = Column(String(255), nullable=False)
    import_type = Column(String(50), nullable=False)  # e.g., 'cmdb', 'asset_inventory'
    description = Column(Text, nullable=True)

    # File metadata (consolidated field names)
    filename = Column(String(255), nullable=False)  # was source_filename
    file_size = Column(Integer, nullable=True)  # was file_size_bytes
    mime_type = Column(String(100), nullable=True)  # was file_type
    source_system = Column(String(100), nullable=True)  # New field for data origin

    # Job status and progress
    status = Column(String(20), nullable=False, default="pending")  # pending, processing, completed, failed
    progress_percentage = Column(Float, default=0.0)
    total_records = Column(Integer, nullable=True)
    processed_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)

    # Configuration and user info
    imported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Error handling (new fields)
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    raw_records = relationship("RawImportRecord", back_populates="data_import", cascade="all, delete-orphan")
    field_mappings = relationship("ImportFieldMapping", back_populates="data_import", cascade="all, delete-orphan")
    discovery_flows = relationship("DiscoveryFlow", back_populates="data_import")
    
    user = relationship("User")
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")
    
    __table_args__ = (
        {"comment": "Tracks data import jobs and their metadata, with multi-tenancy."},
    )


class RawImportRecord(Base):
    """Model for storing individual raw records from an imported file."""

    __tablename__ = "raw_import_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    data_import_id = Column(UUID(as_uuid=True), ForeignKey("data_imports.id", ondelete="CASCADE"), nullable=False)
    
    # Context IDs for direct querying
    client_account_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=True)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("engagements.id"), nullable=True)
    master_flow_id = Column(UUID(as_uuid=True), ForeignKey("crewai_flow_state_extensions.id"), nullable=True)

    row_number = Column(Integer, nullable=False)  # temporarily using old name until migration
    raw_data = Column(JSON, nullable=False)
    cleansed_data = Column(JSON, nullable=True)  # was processed_data
    
    # Validation and processing status
    validation_errors = Column(JSON, nullable=True)
    processing_notes = Column(Text, nullable=True)
    
    # Status tracking
    is_processed = Column(Boolean, default=False)
    is_valid = Column(Boolean, default=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))  # Link to final asset if created
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    data_import = relationship("DataImport", back_populates="raw_records")
    
    __table_args__ = (
        {"comment": "Stores individual raw data records from imported files before processing."},
    )


class ImportProcessingStep(Base):
    """Model to track individual steps in a complex data import workflow."""
    
    __tablename__ = "import_processing_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    data_import_id = Column(UUID(as_uuid=True), ForeignKey("data_imports.id", ondelete="CASCADE"), nullable=False)
    
    step_name = Column(String(100), nullable=False) # e.g., 'validation', 'field_mapping', 'asset_creation'
    step_order = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="pending") # pending, running, completed, failed
    
    description = Column(Text, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    records_processed = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    data_import = relationship("DataImport")

    __table_args__ = (
        {"comment": "Tracks individual processing steps within a data import job for observability."},
    ) 