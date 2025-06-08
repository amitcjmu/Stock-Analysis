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
    
    source_field = Column(String(255), nullable=False)
    target_field = Column(String(255), nullable=False)
    
    mapping_type = Column(String(50), nullable=False, default="direct") # direct, transformation, constant
    confidence_score = Column(Float, nullable=True) # Confidence from AI suggestion
    
    is_user_defined = Column(Boolean, default=False)
    is_validated = Column(Boolean, default=False)
    validation_method = Column(String(50), nullable=True) # e.g., 'user_approved', 'system_validated'
    
    status = Column(String(20), default="suggested") # suggested, approved, rejected, implemented
    
    # Tracking feedback and learning
    user_feedback = Column(Text, nullable=True)
    original_ai_suggestion = Column(String(255), nullable=True)
    correction_reason = Column(Text, nullable=True)
    
    # Advanced mapping details
    transformation_logic = Column(JSON, nullable=True) # For complex transformations
    validation_rules = Column(JSON, nullable=True) # Rules to apply to the mapped field
    sample_values = Column(JSON, nullable=True) # Sample source values for context
    
    suggested_by = Column(String(50), default="ai_agent") # 'ai_agent' or 'user'
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    validated_at = Column(DateTime(timezone=True), nullable=True)
    
    data_import = relationship("DataImport")
    user = relationship("User")

    __table_args__ = (
        {"comment": "Manages field mappings for data imports, including AI suggestions and user overrides."},
    ) 