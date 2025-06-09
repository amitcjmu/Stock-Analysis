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
    session_id = Column(UUID(as_uuid=True), ForeignKey("data_import_sessions.id", ondelete="CASCADE"), nullable=True)

    import_name = Column(String(255), nullable=False)
    import_type = Column(String(50), nullable=False)  # e.g., 'cmdb', 'asset_inventory'
    description = Column(Text, nullable=True)

    # File metadata
    source_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    file_type = Column(String(100), nullable=True)
    file_hash = Column(String(64), nullable=True)

    # Job status and progress
    status = Column(String(20), nullable=False, default="pending")  # pending, processing, completed, failed
    progress_percentage = Column(Float, default=0.0)
    total_records = Column(Integer, nullable=True)
    processed_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)

    # Configuration and user info
    import_config = Column(JSON, nullable=True)
    imported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    is_mock = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    raw_records = relationship("RawImportRecord", back_populates="data_import", cascade="all, delete-orphan")
    session = relationship("DataImportSession", back_populates="data_imports")
    
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
    session_id = Column(UUID(as_uuid=True), ForeignKey("data_import_sessions.id"), nullable=True)

    row_number = Column(Integer, nullable=False)
    record_id = Column(String(255), nullable=True)  # Optional unique ID from source system
    raw_data = Column(JSON, nullable=False)
    processed_data = Column(JSON, nullable=True)
    
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