"""
Pydantic schemas for Engagement and related entities.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

class EngagementSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    start_date: datetime
    end_date: Optional[datetime] = None
    status: str = "active"

    class Config:
        from_attributes = True

class Engagement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    client_account_id: str
    description: Optional[str] = None
    status: str
    start_date: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    sessions: List[EngagementSession] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 