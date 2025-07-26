"""
Agent Task History Model
Tracks detailed execution history for individual agent tasks
Part of the Agent Observability Enhancement
"""

import uuid
from typing import Any, Dict

from sqlalchemy import (
    DECIMAL,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from app.core.database import Base


class AgentTaskHistory(Base):
    """
    Detailed history of all agent task executions for performance tracking and analysis.
    This table captures comprehensive metrics for each task executed by an agent,
    including timing, resource usage, and outcome data.
    """

    __tablename__ = "agent_task_history"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the agent task history record",
    )

    # Task identification
    flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crewai_flow_state_extensions.flow_id"),
        nullable=False,
        index=True,
        comment="Reference to the CrewAI flow this task belongs to",
    )
    agent_name = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Name of the agent that executed the task",
    )
    agent_type = Column(
        String(50), nullable=False, comment="Type of agent: individual or crew_member"
    )
    task_id = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Unique identifier for the task within the flow",
    )
    task_name = Column(
        String(255), nullable=False, comment="Human-readable name of the task"
    )
    task_description = Column(
        Text,
        nullable=True,
        comment="Detailed description of what the task accomplished",
    )

    # Timing information
    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="When the task execution started",
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the task execution completed (null if still running)",
    )
    duration_seconds = Column(
        DECIMAL(10, 3), nullable=True, comment="Total execution time in seconds"
    )

    # Task status and outcome
    status = Column(
        String(50), nullable=False, comment="Current status of the task execution"
    )
    success = Column(
        Boolean, nullable=True, comment="Whether the task completed successfully"
    )
    result_preview = Column(
        Text,
        nullable=True,
        comment="Preview of the task result (truncated for large outputs)",
    )
    error_message = Column(
        Text, nullable=True, comment="Error message if the task failed"
    )
    confidence_score = Column(
        DECIMAL(3, 2),
        nullable=True,
        comment="Agent confidence score for the task result (0-1)",
    )

    # Resource usage metrics
    llm_calls_count = Column(
        Integer,
        nullable=False,
        server_default="0",
        comment="Number of LLM API calls made during task execution",
    )
    thinking_phases_count = Column(
        Integer,
        nullable=False,
        server_default="0",
        comment="Number of thinking/reasoning phases during execution",
    )
    token_usage = Column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="Detailed token usage: {input_tokens, output_tokens, total_tokens}",
    )
    memory_usage_mb = Column(
        DECIMAL(8, 2),
        nullable=True,
        comment="Peak memory usage during task execution in MB",
    )

    # Multi-tenant fields
    client_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("client_accounts.id"),
        nullable=False,
        index=True,
        comment="Client account this task belongs to",
    )
    engagement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("engagements.id"),
        nullable=False,
        index=True,
        comment="Engagement this task is part of",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="When this record was created",
    )

    # Foreign key relationships
    flow = relationship(
        "CrewAIFlowStateExtensions",
        foreign_keys=[flow_id],
        primaryjoin="AgentTaskHistory.flow_id == CrewAIFlowStateExtensions.flow_id",
    )
    client_account = relationship(
        "ClientAccount",
        foreign_keys=[client_account_id],
        primaryjoin="AgentTaskHistory.client_account_id == ClientAccount.id",
    )
    engagement = relationship(
        "Engagement",
        foreign_keys=[engagement_id],
        primaryjoin="AgentTaskHistory.engagement_id == Engagement.id",
    )

    # Check constraints
    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="chk_agent_task_history_confidence_score",
        ),
        CheckConstraint(
            "duration_seconds >= 0", name="chk_agent_task_history_duration_seconds"
        ),
        CheckConstraint(
            "status IN ('pending', 'starting', 'running', 'thinking', 'waiting_llm', 'processing_response', 'completed', 'failed', 'timeout')",
            name="chk_agent_task_history_status",
        ),
        CheckConstraint(
            "agent_type IN ('individual', 'crew_member')",
            name="chk_agent_task_history_agent_type",
        ),
    )

    def __repr__(self):
        return f"<AgentTaskHistory(id={self.id}, agent={self.agent_name}, task={self.task_name}, status={self.status})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "flow_id": str(self.flow_id),
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "task_description": self.task_description,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "duration_seconds": (
                float(self.duration_seconds) if self.duration_seconds else None
            ),
            "status": self.status,
            "success": self.success,
            "result_preview": self.result_preview,
            "error_message": self.error_message,
            "confidence_score": (
                float(self.confidence_score) if self.confidence_score else None
            ),
            "llm_calls_count": self.llm_calls_count,
            "thinking_phases_count": self.thinking_phases_count,
            "token_usage": self.token_usage or {},
            "memory_usage_mb": (
                float(self.memory_usage_mb) if self.memory_usage_mb else None
            ),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def calculate_duration(self):
        """Calculate and set duration based on start and end times"""
        if self.started_at and self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.duration_seconds = round(duration, 3)

    def update_token_usage(self, input_tokens: int, output_tokens: int):
        """Update token usage metrics"""
        if not self.token_usage:
            self.token_usage = {}

        current_input = self.token_usage.get("input_tokens", 0)
        current_output = self.token_usage.get("output_tokens", 0)

        self.token_usage = {
            "input_tokens": current_input + input_tokens,
            "output_tokens": current_output + output_tokens,
            "total_tokens": current_input
            + current_output
            + input_tokens
            + output_tokens,
        }
