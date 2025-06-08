"""
Data Quality Issue Model
"""
import uuid as uuid_pkg
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    JSON,
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

class DataQualityIssue(Base):
    """Model to track data quality issues identified during import."""
    
    __tablename__ = "data_quality_issues"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    data_import_id = Column(UUID(as_uuid=True), ForeignKey("data_imports.id", ondelete="CASCADE"), nullable=False)
    raw_record_id = Column(UUID(as_uuid=True), ForeignKey("raw_import_records.id"), nullable=True)

    issue_type = Column(String(50), nullable=False) # e.g., 'missing_value', 'invalid_format', 'inconsistent_data'
    field_name = Column(String(255), nullable=True)
    current_value = Column(Text, nullable=True)
    suggested_value = Column(Text, nullable=True)
    
    severity = Column(String(20), default="medium") # low, medium, high, critical
    confidence_score = Column(Float, nullable=True) # AI confidence in the issue/suggestion
    reasoning = Column(Text, nullable=True) # Explanation from AI
    
    status = Column(String(20), default="detected") # detected, resolved, ignored
    
    resolution_method = Column(String(50), nullable=True) # e.g., 'user_corrected', 'auto_cleaned', 'ignored'
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    data_import = relationship("DataImport")
    raw_record = relationship("RawImportRecord")
    user = relationship("User")
    
    __table_args__ = (
        {"comment": "Tracks data quality issues identified during the import process."},
    ) 