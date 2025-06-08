"""
Models for storing learned patterns from AI agents.
"""

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class MappingLearningPattern(Base):
    __tablename__ = 'mapping_learning_patterns'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_column = Column(String(255), nullable=False, index=True)
    target_column = Column(String(255), nullable=False, index=True)
    pattern_type = Column(String(50), nullable=False, comment="e.g., 'regex', 'value_map', 'synonym'")
    pattern_details = Column(JSON, nullable=False, comment="Details of the learned pattern, e.g., the regex string or a value mapping dictionary")
    confidence_score = Column(JSON) # Using JSON to store more complex score structures
    
    created_by = Column(String(100), nullable=False, comment="Identifier for the agent or user who created the pattern")
    last_used_at = Column(DateTime(timezone=True), server_default=func.now())
    usage_count = Column(JSON) # Using JSON to store more complex count structures
    
    # Foreign key to link to an engagement if patterns are engagement-specific
    engagement_id = Column(UUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<MappingLearningPattern(source='{self.source_column}', target='{self.target_column}', type='{self.pattern_type}')>" 