"""
Context API Schemas

Pydantic models for context-related API requests and responses.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


# Response models for context switcher
class ClientResponse(BaseModel):
    """Client information response"""
    id: str
    name: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    status: str = "active"


class EngagementResponse(BaseModel):
    """Engagement information response"""
    id: str
    name: str
    client_id: str
    status: str
    type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ClientsListResponse(BaseModel):
    """List of clients response"""
    clients: List[ClientResponse]


class EngagementsListResponse(BaseModel):
    """List of engagements response"""
    engagements: List[EngagementResponse]


class UpdateUserDefaultsRequest(BaseModel):
    """Request to update user default context"""
    client_id: Optional[str] = None
    engagement_id: Optional[str] = None


class UpdateUserDefaultsResponse(BaseModel):
    """Response after updating user defaults"""
    message: str
    updated_fields: Dict[str, Any]


class ValidateContextRequest(BaseModel):
    """Request to validate context"""
    client_id: Optional[str] = None
    engagement_id: Optional[str] = None
    user_id: Optional[str] = None


class ValidateContextResponse(BaseModel):
    """Context validation response"""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []