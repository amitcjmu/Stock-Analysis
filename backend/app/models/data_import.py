"""
Data Import Models
Models for capturing raw import data and processing steps in the Discovery phase.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from app.core.database import Base

class ImportStatus(str, PyEnum):
    """Import processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    VALIDATED = "validated"
    ARCHIVED = "archived"

class ImportType(str, PyEnum):
    """Type of import data."""
    CMDB = "cmdb"
    APPLICATION_SCAN = "application_scan"
    MIGRATION_DISCOVERY = "migration_discovery"
    DOCUMENTATION = "documentation"
    MONITORING = "monitoring"
    CUSTOM = "custom"

class DataImport(Base):
    """
    Main table for tracking data import sessions.
    Captures metadata about each import operation.
    """
    __tablename__ = "data_imports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    client_account_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id", ondelete="CASCADE"), nullable=True)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=True)
    
    # Session reference (Task 1.1.4) 
    session_id = Column(UUID(as_uuid=True), ForeignKey("data_import_sessions.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Import metadata
    import_name = Column(String(255), nullable=False)
    import_type = Column(String(50), nullable=False)  # ImportType enum
    description = Column(Text)
    
    # Source file information
    source_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer)
    file_type = Column(String(100))
    file_hash = Column(String(64))  # SHA-256 hash for deduplication
    
    # Processing status
    status = Column(String(20), default=ImportStatus.UPLOADED, nullable=False)
    progress_percentage = Column(Float, default=0.0)
    
    # Statistics
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    
    # Processing configuration
    import_config = Column(JSON)  # Parser settings, field mappings, etc.
    
    # Audit trail
    imported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Context flags
    is_mock = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client_account = relationship("ClientAccount", back_populates="data_imports")
    engagement = relationship("Engagement", back_populates="data_imports") 
    session = relationship("DataImportSession", back_populates="data_imports")  # Task 1.1.4
    imported_by_user = relationship("User")
    raw_records = relationship("RawImportRecord", back_populates="data_import", cascade="all, delete-orphan")
    processing_steps = relationship("ImportProcessingStep", back_populates="data_import", cascade="all, delete-orphan")
    field_mappings = relationship("ImportFieldMapping", back_populates="data_import", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DataImport(id={self.id}, name='{self.import_name}', status='{self.status}')>"

class RawImportRecord(Base):
    """
    Stores raw, unprocessed records exactly as imported.
    This preserves the original source data as reference.
    """
    __tablename__ = "raw_import_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    data_import_id = Column(UUID(as_uuid=True), ForeignKey("data_imports.id", ondelete="CASCADE"), nullable=False)
    
    # Record identification
    row_number = Column(Integer, nullable=False)  # Original row position in source
    record_id = Column(String(255))  # Business identifier if available
    
    # Raw data (exactly as imported)
    raw_data = Column(JSON, nullable=False)  # Complete original record
    
    # Processing results
    processed_data = Column(JSON)  # Cleaned/mapped version
    validation_errors = Column(JSON)  # Any validation issues
    processing_notes = Column(Text)  # AI insights, warnings, etc.
    
    # Status tracking
    is_processed = Column(Boolean, default=False)
    is_valid = Column(Boolean, default=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))  # Link to final asset if created
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Relationships
    data_import = relationship("DataImport", back_populates="raw_records")
    asset = relationship("Asset")
    
    def __repr__(self):
        return f"<RawImportRecord(id={self.id}, row={self.row_number}, processed={self.is_processed})>"

class ImportProcessingStep(Base):
    """
    Tracks each step in the data processing pipeline.
    Provides audit trail and debugging information.
    """
    __tablename__ = "import_processing_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    data_import_id = Column(UUID(as_uuid=True), ForeignKey("data_imports.id", ondelete="CASCADE"), nullable=False)
    
    # Step information
    step_name = Column(String(100), nullable=False)  # e.g., "file_parsing", "field_mapping", "validation"
    step_order = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)  # success, failed, skipped
    
    # Step details
    description = Column(Text)
    input_data = Column(JSON)  # Input parameters
    output_data = Column(JSON)  # Results or artifacts
    error_details = Column(JSON)  # Error information if failed
    
    # Performance metrics
    records_processed = Column(Integer, default=0)
    duration_seconds = Column(Float)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    data_import = relationship("DataImport", back_populates="processing_steps")
    
    def __repr__(self):
        return f"<ImportProcessingStep(id={self.id}, step='{self.step_name}', status='{self.status}')>"

class ImportFieldMapping(Base):
    """
    Stores field mapping decisions for each import.
    Enables learning and reuse of mappings.
    """
    __tablename__ = "import_field_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    data_import_id = Column(UUID(as_uuid=True), ForeignKey("data_imports.id", ondelete="CASCADE"), nullable=False)
    
    # Mapping details
    source_field = Column(String(255), nullable=False)  # Original field name
    target_field = Column(String(255), nullable=False)  # Mapped canonical field
    mapping_type = Column(String(50), nullable=False)  # direct, computed, concatenated, etc.
    
    # Mapping confidence and validation
    confidence_score = Column(Float, default=0.0)  # AI confidence in mapping
    is_user_defined = Column(Boolean, default=False)  # User created/corrected mapping
    is_validated = Column(Boolean, default=False)  # User confirmed mapping
    validation_method = Column(String(50))  # user, ai, rule_based
    status = Column(String(20), default="pending")  # pending, approved, rejected
    
    # Learning and feedback
    user_feedback = Column(Text)  # User notes about the mapping
    original_ai_suggestion = Column(String(255))  # What AI originally suggested
    correction_reason = Column(Text)  # Why user corrected the mapping
    
    # Transformation details
    transformation_logic = Column(JSON)  # Any data transformation applied
    validation_rules = Column(JSON)  # Field validation rules
    sample_values = Column(JSON)  # Sample source values for reference
    
    # Learning metadata
    suggested_by = Column(String(50))  # ai, user, template
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    validated_at = Column(DateTime(timezone=True))
    
    # Relationships
    data_import = relationship("DataImport", back_populates="field_mappings")
    validator = relationship("User")
    
    def __repr__(self):
        return f"<ImportFieldMapping(id={self.id}, {self.source_field} -> {self.target_field})>"

class DataQualityIssue(Base):
    """
    Tracks data quality issues found during import processing.
    """
    __tablename__ = "data_quality_issues"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    data_import_id = Column(UUID(as_uuid=True), ForeignKey("data_imports.id", ondelete="CASCADE"), nullable=False)
    raw_record_id = Column(UUID(as_uuid=True), ForeignKey("raw_import_records.id"), nullable=True)
    
    # Issue details
    issue_type = Column(String(50), nullable=False)  # missing_data, format_error, duplicate, etc.
    field_name = Column(String(255))
    current_value = Column(Text)
    suggested_value = Column(Text)
    
    # Issue metadata
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    confidence_score = Column(Float, default=0.0)
    reasoning = Column(Text)
    
    # Resolution tracking
    status = Column(String(20), default="pending")  # pending, resolved, ignored
    resolution_method = Column(String(50))  # auto, manual, rule
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolution_notes = Column(Text)
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    data_import = relationship("DataImport")
    raw_record = relationship("RawImportRecord")
    resolver = relationship("User")
    
    def __repr__(self):
        return f"<DataQualityIssue(id={self.id}, type='{self.issue_type}', status='{self.status}')>"

class CustomTargetField(Base):
    """
    User-defined target fields that extend the standard CMDB schema.
    This enables dynamic field creation based on user discoveries.
    """
    __tablename__ = "custom_target_fields"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    client_account_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id", ondelete="CASCADE"), nullable=False)
    
    # Field definition
    field_name = Column(String(255), nullable=False, unique=True, index=True)
    field_type = Column(String(50), nullable=False)  # string, integer, float, boolean, date, json
    description = Column(Text)
    
    # Field metadata
    is_required = Column(Boolean, default=False)
    is_searchable = Column(Boolean, default=True)
    is_critical = Column(Boolean, default=False)  # Affects data quality scoring
    
    # Learning metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    usage_count = Column(Integer, default=0)  # How often this field is mapped
    success_rate = Column(Float, default=0.0)  # Quality of mappings using this field
    
    # Validation rules (dynamic)
    validation_schema = Column(JSON)  # JSON schema for validation
    default_value = Column(Text)
    allowed_values = Column(JSON)  # For enum-like fields
    
    # AI learning data
    common_source_patterns = Column(JSON)  # Source field names that commonly map here
    sample_values = Column(JSON)  # Examples of good values for this field
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True))
    
    # Relationships
    client_account = relationship("ClientAccount")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<CustomTargetField(id={self.id}, name='{self.field_name}', type='{self.field_type}')>"

class MappingLearningPattern(Base):
    """
    Stores AI learning patterns from user corrections.
    This enables the system to get smarter over time.
    """
    __tablename__ = "mapping_learning_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    client_account_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id", ondelete="CASCADE"), nullable=False)
    
    # Pattern identification
    source_field_pattern = Column(String(255), nullable=False, index=True)  # Regex or exact match
    content_pattern = Column(JSON)  # Sample values, data types, formats
    target_field = Column(String(255), nullable=False, index=True)
    
    # Learning metadata
    pattern_confidence = Column(Float, default=0.0)  # How reliable this pattern is
    success_count = Column(Integer, default=0)  # Times this pattern was correct
    failure_count = Column(Integer, default=0)  # Times this pattern was wrong
    
    # Pattern context
    learned_from_mapping_id = Column(UUID(as_uuid=True), ForeignKey("import_field_mappings.id"))
    user_feedback = Column(Text)  # Why this pattern is good/bad
    
    # Pattern rules (AI learns these)
    matching_rules = Column(JSON)  # Complex matching logic
    transformation_hints = Column(JSON)  # How to transform data
    quality_checks = Column(JSON)  # Validation rules for this mapping
    
    # Usage tracking
    times_applied = Column(Integer, default=0)
    last_applied_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client_account = relationship("ClientAccount")
    learned_from_mapping = relationship("ImportFieldMapping")
    
    def update_success_rate(self):
        """Calculate and update the confidence score based on success/failure ratio."""
        total = self.success_count + self.failure_count
        if total > 0:
            self.pattern_confidence = self.success_count / total
        return self.pattern_confidence
    
    def __repr__(self):
        return f"<MappingLearningPattern(id={self.id}, '{self.source_field_pattern}' -> '{self.target_field}', confidence={self.pattern_confidence})>" 