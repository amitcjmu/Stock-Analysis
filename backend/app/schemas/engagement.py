"""
Pydantic schemas for Engagement and related entities.
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import uuid
from enum import Enum

class EngagementStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"

class EngagementType(str, Enum):
    MIGRATION = "migration"
    ASSESSMENT = "assessment"
    DISCOVERY = "discovery"
    OPTIMIZATION = "optimization"
    OTHER = "other"

class EngagementSession(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    start_date: datetime
    end_date: Optional[datetime] = None
    status: str = "active"

class EngagementBase(BaseModel):
    """Base model for engagement data"""
    name: str = Field(..., min_length=3, max_length=255)
    client_account_id: str = Field(..., description="ID of the client account this engagement belongs to")
    engagement_type: EngagementType = Field(default=EngagementType.ASSESSMENT)
    status: EngagementStatus = Field(default=EngagementStatus.PLANNING)
    description: Optional[str] = Field(None, max_length=2000)
    start_date: Optional[date] = None
    target_completion_date: Optional[date] = None
    budget: Optional[float] = Field(None, ge=0, description="Budget amount in the specified currency")
    budget_currency: str = Field(default="USD", max_length=3, description="ISO currency code")
    project_manager: Optional[str] = Field(None, max_length=255, description="Name or ID of the project manager")
    risk_level: Optional[str] = Field("medium", pattern="^(low|medium|high)$")
    is_active: bool = Field(default=True)
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('target_completion_date')
    def validate_dates(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v < values['start_date']:
            raise ValueError('target_completion_date cannot be before start_date')
        return v

class EngagementCreate(EngagementBase):
    """Schema for creating a new engagement"""
    pass

class EngagementUpdate(BaseModel):
    """Schema for updating an existing engagement"""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    status: Optional[EngagementStatus] = None
    description: Optional[str] = Field(None, max_length=2000)
    start_date: Optional[date] = None
    target_completion_date: Optional[date] = None
    budget: Optional[float] = Field(None, ge=0)
    budget_currency: Optional[str] = Field(None, max_length=3)
    project_manager: Optional[str] = Field(None, max_length=255)
    risk_level: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class Engagement(EngagementBase):
    """Full engagement model with all fields"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: str = Field(..., description="ID of the user who created the engagement")
    updated_by: Optional[str] = Field(None, description="ID of the user who last updated the engagement")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    sessions: List[EngagementSession] = Field(default_factory=list)

class EngagementResponse(Engagement):
    """Response model for engagement data"""
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Cloud Migration Project",
                "client_account_id": "550e8400-e29b-41d4-a716-446655440001",
                "engagement_type": "migration",
                "status": "planning",
                "description": "Full migration to cloud infrastructure",
                "start_date": "2023-01-15",
                "target_completion_date": "2023-12-31",
                "budget": 500000.0,
                "budget_currency": "USD",
                "project_manager": "John Doe",
                "risk_level": "medium",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        }