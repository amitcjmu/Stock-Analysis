"""
Context Schemas

Pydantic models for user context data.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from .flow import FlowBase

class ClientBase(BaseModel):
    """Client account information."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class EngagementBase(BaseModel):
    """Engagement information."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: Optional[str] = None
    client_id: UUID
    created_at: datetime
    updated_at: datetime

class SessionBase(BaseModel):
    """Session information."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: Optional[str] = None
    engagement_id: UUID
    is_default: bool = False
    created_by: UUID
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
