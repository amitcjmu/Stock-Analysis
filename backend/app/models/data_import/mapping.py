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
    Stores a mapping between a source field from an imported file and a target
    field in the system's data model. It tracks AI suggestions, user approvals,
    and any transformation rules.
    """
    
    __tablename__ = "import_field_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4, comment="Unique identifier for the field mapping record.")
    data_import_id = Column(UUID(as_uuid=True), ForeignKey("data_imports.id", ondelete="CASCADE"), nullable=False, comment="Foreign key to the parent data import job.")
    client_account_id = Column(UUID(as_uuid=True), nullable=False, comment="Denormalized client account ID for efficient multi-tenant queries.")
    master_flow_id = Column(UUID(as_uuid=True), ForeignKey("crewai_flow_state_extensions.id"), nullable=True, comment="The master flow ID this mapping is associated with.")
    
    source_field = Column(String(255), nullable=False, comment="The name of the field in the source file (e.g., a CSV column header).")
    target_field = Column(String(255), nullable=False, comment="The name of the target field in the system's data model (e.g., 'asset.name').")
    
    match_type = Column(String(50), nullable=False, default="direct", comment="The type of match (e.g., 'direct', 'inferred', 'manual').")
    confidence_score = Column(Float, nullable=True, comment="A score from 0.0 to 1.0 indicating the AI's confidence in a suggested mapping.")
    
    status = Column(String(20), default="suggested", comment="The current status of the mapping (e.g., 'suggested', 'approved', 'rejected').")
    suggested_by = Column(String(50), default="ai_mapper", comment="Indicates who suggested the mapping (e.g., 'ai_mapper', 'user').")
    
    # Approval workflow (simplified)
    approved_by = Column(String(255), nullable=True, comment="The user ID of the person who approved this mapping.")
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="Timestamp when the mapping was approved.")
    transformation_rules = Column(JSON, nullable=True, comment="A JSON blob defining any transformation logic to be applied to the data (e.g., data type casting, value replacements).")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Timestamp when the mapping record was created.")
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), comment="Timestamp of the last update to this record.")
    
    # Relationships
    data_import = relationship("DataImport", back_populates="field_mappings")

    __table_args__ = (
        {"comment": "Stores mappings between source data fields and target system fields for data imports."},
    ) 