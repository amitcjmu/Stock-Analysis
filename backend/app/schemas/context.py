"""
Context Schemas

Pydantic models for user context data.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .flow import FlowBase


class ClientBase(BaseModel):
    """Client account information."""

    model_config = ConfigDict(from_attributes=True)

    id: str  # Changed from UUID to str to match implementation
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EngagementBase(BaseModel):
    """Engagement information."""

    model_config = ConfigDict(from_attributes=True)

    id: str  # Changed from UUID to str to match implementation
    name: str
    description: Optional[str] = None
    client_id: str  # Changed from UUID to str to match implementation
    created_at: datetime
    updated_at: datetime


class SessionBase(BaseModel):
    """Session information."""

    model_config = ConfigDict(from_attributes=True)

    id: str  # Changed from UUID to str to match implementation
    name: str
    description: Optional[str] = None
    engagement_id: str  # Changed from UUID to str to match implementation
    is_default: bool = False
    created_by: str  # Changed from UUID to str to match implementation
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class UserContext(BaseModel):
    """Complete user context including client, engagement, and flows."""

    model_config = ConfigDict(from_attributes=True)

    user: Dict[str, Any]
    client: Optional[ClientBase] = None
    engagement: Optional[EngagementBase] = None
    active_flows: List[FlowBase] = Field(default_factory=list)
    current_flow: Optional[FlowBase] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert UserContext to dictionary for serialization."""
        result = {
            "user": self.user,
            "client": self.client.model_dump() if self.client else None,
            "engagement": self.engagement.model_dump() if self.engagement else None,
            "active_flows": [flow.model_dump() for flow in self.active_flows if flow],
            "current_flow": (
                self.current_flow.model_dump() if self.current_flow else None
            ),
        }
        return result
