"""
Assessment Flow Event Streaming Pydantic schemas.

This module contains schemas for real-time event streaming
during assessment flow execution.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.assessment_flow import AssessmentPhase


class AssessmentFlowEvent(BaseModel):
    """Schema for assessment flow events."""

    flow_id: str
    event_type: str = Field(..., description="Type of event")
    phase: AssessmentPhase
    timestamp: datetime
    data: Dict[str, Any] = Field(default={}, description="Event data")
    message: Optional[str] = Field(None, description="Human-readable message")

    model_config = ConfigDict(use_enum_values=True)


class AgentProgressEvent(BaseModel):
    """Schema for agent progress events."""

    flow_id: str
    agent_name: str
    task_name: str
    progress_percentage: float = Field(ge=0, le=100)
    status: str = Field(..., description="Agent status")
    timestamp: datetime
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
