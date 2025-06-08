"""
Data Import Session Model
"""
import uuid as uuid_pkg
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    ForeignKey,
    UUID,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from app.core.database import Base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()

class DataImportSession(Base):
    """Represents a full data import session, grouping multiple file uploads."""
    
    __tablename__ = "data_import_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    client_account_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("engagements.id"), nullable=False)
    
    session_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    status = Column(String(20), default="ongoing", nullable=False) # e.g., ongoing, completed, failed
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    imports = relationship("DataImport", back_populates="session")
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")
    user = relationship("User")

    def __repr__(self):
        return f"<DataImportSession(id={self.id}, name='{self.session_name}', status='{self.status}')>" 