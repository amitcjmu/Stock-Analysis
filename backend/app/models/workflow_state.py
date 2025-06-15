"""
Database model for persisting workflow state.
"""
import uuid
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class WorkflowState(Base):
    """
    Represents the state of a single workflow instance in the database.
    """
    __tablename__ = 'workflow_states'

    id = Column(Integer, primary_key=True, index=True)
    
    session_id = Column(String, unique=True, index=True, nullable=False)
    client_account_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    engagement_id = Column(UUID(as_uuid=True), index=True, nullable=False)

    workflow_type = Column(String, default="discovery", nullable=False, index=True)
    current_phase = Column(String, nullable=False)
    status = Column(String, default="running", nullable=False, index=True) # e.g., running, completed, failed
    
    state_data = Column(JSON, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<WorkflowState(id={self.id}, session_id={self.session_id}, status='{self.status}')>" 