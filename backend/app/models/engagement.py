"""
Engagement Model
"""

import uuid
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Boolean, Text,
    Integer, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Engagement(Base):
    __tablename__ = 'engagements'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    client_account_id = Column(UUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=False)
    
    status = Column(String(50), default='pending')
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    
    primary_contact_email = Column(String(255))
    technical_lead_email = Column(String(255))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    client_account = relationship("ClientAccount", back_populates="engagements")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('client_account_id', 'name', name='_client_engagement_name_uc'),
    )
    
    def __repr__(self):
        return f"<Engagement(id={self.id}, name='{self.name}', client_id='{self.client_account_id}')>" 