"""
Context Schemas

Pydantic models for user context data.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

class ClientBase(BaseModel):
    """Client account information."""
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EngagementBase(BaseModel):
    """Engagement information."""
    id: UUID
    name: str
    description: Optional[str] = None
    client_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SessionBase(BaseModel):
    """Session information."""
    id: UUID
    name: str
    description: Optional[str] = None
    engagement_id: UUID
    is_default: bool = False
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class UserContext(BaseModel):
    """Complete user context including client, engagement, and session."""
    user: Dict[str, Any]
    client: Optional[ClientBase] = None
    engagement: Optional[EngagementBase] = None
    session: Optional[SessionBase] = None
    available_sessions: List[SessionBase] = Field(default_factory=list)

    class Config:
        from_attributes = True
