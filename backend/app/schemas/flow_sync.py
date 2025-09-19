"""
Flow Synchronization Schemas
Pydantic models for flow synchronization and issue tracking operations.
"""

from typing import Any, Callable, Dict, Literal, Optional
from pydantic import BaseModel, Field


class FlowIssue(BaseModel):
    """Schema for flow synchronization issues."""

    issue_type: str = Field(..., description="Type of synchronization issue")
    description: str = Field(..., description="Detailed description of the issue")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Issue severity level"
    )
    suggested_action: str = Field(
        ..., description="Recommended action to resolve the issue"
    )
    flow_id: Optional[str] = Field(
        None, description="Flow ID associated with the issue"
    )
    timestamp: Optional[str] = Field(
        None, description="Timestamp when issue was detected"
    )

    class Config:
        from_attributes = True
        json_encoders: Dict[Any, Callable[[Any], Any]] = {
            # Add any custom encoders if needed
        }
