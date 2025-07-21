"""
Agent Performance Daily Model
Daily aggregated performance metrics for each agent
Part of the Agent Observability Enhancement
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, func, Integer, Date, DECIMAL, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
import uuid
from datetime import datetime, date
from typing import Dict, Any

from app.core.database import Base


class AgentPerformanceDaily(Base):
    """
    Daily aggregated performance metrics for each agent.
    This table stores summarized metrics calculated from agent_task_history
    to provide quick access to agent performance trends.
    """
    __tablename__ = "agent_performance_daily"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                comment="Unique identifier for the daily performance record")
    
    # Agent identification
    agent_name = Column(String(100), nullable=False, index=True,
                        comment="Name of the agent")
    date_recorded = Column(Date, nullable=False, index=True,
                           comment="Date for which metrics are aggregated")
    
    # Task metrics
    tasks_attempted = Column(Integer, nullable=False, server_default='0',
                             comment="Total number of tasks attempted")
    tasks_completed = Column(Integer, nullable=False, server_default='0',
                             comment="Number of successfully completed tasks")
    tasks_failed = Column(Integer, nullable=False, server_default='0',
                          comment="Number of failed tasks")
    
    # Performance metrics
    avg_duration_seconds = Column(DECIMAL(10, 3), nullable=True,
                                  comment="Average task duration in seconds")
    avg_confidence_score = Column(DECIMAL(3, 2), nullable=True,
                                  comment="Average confidence score across all tasks")
    success_rate = Column(DECIMAL(5, 2), nullable=True,
                          comment="Success rate percentage (0-100)")
    
    # Resource usage metrics
    total_llm_calls = Column(Integer, nullable=False, server_default='0',
                             comment="Total LLM API calls made")
    total_tokens_used = Column(Integer, nullable=False, server_default='0',
                               comment="Total tokens consumed")
    
    # Multi-tenant fields
    client_account_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id"), 
                               nullable=False, index=True,
                               comment="Client account these metrics belong to")
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("engagements.id"), 
                           nullable=False, index=True,
                           comment="Engagement these metrics are part of")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                        comment="When this record was created")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                        comment="When this record was last updated")
    
    # Foreign key relationships
    client_account = relationship("ClientAccount", foreign_keys=[client_account_id],
                                  primaryjoin="AgentPerformanceDaily.client_account_id == ClientAccount.id")
    engagement = relationship("Engagement", foreign_keys=[engagement_id],
                              primaryjoin="AgentPerformanceDaily.engagement_id == Engagement.id")
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('agent_name', 'date_recorded', 'client_account_id', 'engagement_id',
                         name='uq_agent_performance_daily_agent_date_client_engagement'),
        CheckConstraint('success_rate >= 0 AND success_rate <= 100',
                        name='chk_agent_performance_daily_success_rate'),
    )
    
    def __repr__(self):
        return f"<AgentPerformanceDaily(agent={self.agent_name}, date={self.date_recorded}, success_rate={self.success_rate}%)>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "agent_name": self.agent_name,
            "date_recorded": self.date_recorded.isoformat() if self.date_recorded else None,
            "tasks_attempted": self.tasks_attempted,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "avg_duration_seconds": float(self.avg_duration_seconds) if self.avg_duration_seconds else None,
            "avg_confidence_score": float(self.avg_confidence_score) if self.avg_confidence_score else None,
            "success_rate": float(self.success_rate) if self.success_rate else None,
            "total_llm_calls": self.total_llm_calls,
            "total_tokens_used": self.total_tokens_used,
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def calculate_success_rate(self):
        """Calculate and update success rate based on completed and attempted tasks"""
        if self.tasks_attempted > 0:
            self.success_rate = round((self.tasks_completed / self.tasks_attempted) * 100, 2)
        else:
            self.success_rate = 0.0
    
    def update_from_tasks(self, tasks_data: list):
        """Update metrics from a list of task data"""
        if not tasks_data:
            return
        
        self.tasks_attempted = len(tasks_data)
        self.tasks_completed = sum(1 for task in tasks_data if task.get('success') is True)
        self.tasks_failed = sum(1 for task in tasks_data if task.get('success') is False)
        
        # Calculate average duration
        durations = [task.get('duration_seconds', 0) for task in tasks_data if task.get('duration_seconds')]
        if durations:
            self.avg_duration_seconds = round(sum(durations) / len(durations), 3)
        
        # Calculate average confidence score
        confidence_scores = [task.get('confidence_score', 0) for task in tasks_data if task.get('confidence_score')]
        if confidence_scores:
            self.avg_confidence_score = round(sum(confidence_scores) / len(confidence_scores), 2)
        
        # Sum up resource usage
        self.total_llm_calls = sum(task.get('llm_calls_count', 0) for task in tasks_data)
        self.total_tokens_used = sum(
            task.get('token_usage', {}).get('total_tokens', 0) for task in tasks_data
        )
        
        # Calculate success rate
        self.calculate_success_rate()