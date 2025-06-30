"""
Data Import Field Mapping Model
"""
import uuid as uuid_pkg
from datetime import datetime
from sqlalchemy import (
    Column,
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

class ImportFieldMapping(Base):
    """
    Model to store and manage field mappings for data imports,
    including AI suggestions and user overrides.
    """
    
    __tablename__ = "import_field_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    data_import_id = Column(UUID(as_uuid=True), ForeignKey("data_imports.id", ondelete="CASCADE"), nullable=False)
    client_account_id = Column(UUID(as_uuid=True), nullable=False)  # Added for multi-tenancy
    master_flow_id = Column(UUID(as_uuid=True), ForeignKey("crewai_flow_state_extensions.id"), nullable=True)
    
    source_field = Column(String(255), nullable=False)
    target_field = Column(String(255), nullable=False)
    
    match_type = Column(String(50), nullable=False, default="direct")  # was mapping_type
    confidence_score = Column(Float, nullable=True)  # Confidence from AI suggestion
    
    status = Column(String(20), default="suggested")  # suggested, approved, rejected, implemented
    suggested_by = Column(String(50), default="ai_mapper")
    
    # Approval workflow (simplified)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    transformation_rules = Column(JSON, nullable=True)  # Replaces validation_rules and transformation_logic
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relationships
    data_import = relationship("DataImport", back_populates="field_mappings")

    __table_args__ = (
        {"comment": "Manages field mappings for data imports, including AI suggestions and user overrides."},
    ) 