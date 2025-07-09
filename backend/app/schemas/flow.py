"""
Flow Schemas

Pydantic models for flow-based architecture replacing session-based patterns.
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum

class FlowType(str, Enum):
    """Types of flows supported by the platform."""
    DISCOVERY = "discovery"
    ASSESSMENT = "assessment" 
    PLANNING = "planning"
    EXECUTION = "execution"
    MODERNIZE = "modernize"
    FINOPS = "finops"
    OBSERVABILITY = "observability"
    DECOMMISSION = "decommission"

class FlowStatus(str, Enum):
    """Status states for flows."""
    PENDING = "pending"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"
    CANCELLED = "cancelled"

class FlowBase(BaseModel):
    """Base flow information."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    flow_type: FlowType
    status: FlowStatus = FlowStatus.PENDING
    engagement_id: UUID
    created_by: UUID
    metadata: Optional[Dict[str, Any]] = None

class FlowCreate(BaseModel):
    """Schema for creating a new flow."""
    name: str
    flow_type: FlowType
    engagement_id: UUID
    metadata: Optional[Dict[str, Any]] = None

class FlowUpdate(BaseModel):
    """Schema for updating an existing flow."""
    name: Optional[str] = None
    status: Optional[FlowStatus] = None
    metadata: Optional[Dict[str, Any]] = None

class Flow(FlowBase):
    """Complete flow information with timestamps."""
    created_at: datetime
    updated_at: datetime

class FlowInDB(Flow):
    """Flow as stored in database."""
    pass

class FlowList(BaseModel):
    """List of flows with metadata."""
    flows: List[Flow]
    total: int
    engagement_id: UUID