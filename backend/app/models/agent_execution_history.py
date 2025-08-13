"""
Agent Execution History Model

Tracks individual agent task executions for performance monitoring
and analytics. Used by the agent observability dashboard.

CC: Model for agent performance tracking
"""

from datetime import datetime
from typing import Dict, Any
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, JSON, Text, Float, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.base import Base


class AgentExecutionHistory(Base):
    """
    Records individual agent task executions for monitoring and analytics.

    Captures:
    - Task execution details
    - Performance metrics
    - Error information
    - Multi-tenant context
    """

    __tablename__ = "agent_execution_history"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Multi-tenant context
    client_account_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=True)
    flow_id = Column(PGUUID(as_uuid=True), nullable=True)

    # Agent information
    agent_name = Column(String(255), nullable=False, index=True)
    agent_type = Column(String(100), nullable=True)
    agent_phase = Column(String(100), nullable=True)

    # Task information
    task_id = Column(String(255), nullable=True, index=True)
    task_name = Column(String(255), nullable=True)
    task_type = Column(String(100), nullable=True)

    # Execution details
    status = Column(
        String(50), nullable=False, default="pending"
    )  # pending, running, completed, failed
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Performance metrics
    memory_usage_mb = Column(Float, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)
    llm_calls_count = Column(Integer, nullable=True, default=0)
    confidence_score = Column(Float, nullable=True)

    # Results and errors
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Additional metadata (renamed from 'metadata' which is reserved in SQLAlchemy)
    task_metadata = Column("metadata", JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": str(self.id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "flow_id": str(self.flow_id) if self.flow_id else None,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "agent_phase": self.agent_phase,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "task_type": self.task_type,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "llm_calls_count": self.llm_calls_count,
            "confidence_score": self.confidence_score,
            "result": self.result,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "metadata": self.task_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
