"""
Pydantic models for context establishment endpoints.

Response models used across client, engagement, and context update endpoints.
"""

from typing import List, Optional

from pydantic import BaseModel


class ClientResponse(BaseModel):
    """Response model for client information."""

    id: str
    name: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    status: str = "active"


class EngagementResponse(BaseModel):
    """Response model for engagement information."""

    id: str
    name: str
    client_id: str
    status: str
    type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ClientsListResponse(BaseModel):
    """Response model for list of clients."""

    clients: List[ClientResponse]


class EngagementsListResponse(BaseModel):
    """Response model for list of engagements."""

    engagements: List[EngagementResponse]


class ContextUpdateRequest(BaseModel):
    """Request model for updating user context."""

    client_id: str
    engagement_id: str


class ContextUpdateResponse(BaseModel):
    """Response model for context update operation."""

    status: str
    message: str
    client_id: str
    engagement_id: str
