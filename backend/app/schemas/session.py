"""
Pydantic models for Data Import Session API responses and requests.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.data_import_session import SessionType, SessionStatus


class SessionBase(BaseModel):
    """Base model for session data."""
    session_name: str = Field(..., description="Unique identifier for the session")
    session_display_name: Optional[str] = Field(
        None, 
        description="User-friendly display name for the session"
    )
    description: Optional[str] = Field(None, description="Description of the session")
    engagement_id: UUID = Field(..., description="ID of the engagement this session belongs to")
    client_account_id: UUID = Field(..., description="ID of the client account")
    is_default: bool = Field(False, description="Whether this is the default session for the engagement")
    session_type: SessionType = Field(SessionType.DATA_IMPORT, description="Type of session")
    status: SessionStatus = Field(SessionStatus.ACTIVE, description="Current status of the session")
    auto_created: bool = Field(False, description="Whether this session was auto-created")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SessionCreate(SessionBase):
    """Model for creating a new session."""
    pass


class SessionUpdate(BaseModel):
    """Model for updating an existing session."""
    session_display_name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    status: Optional[SessionStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionInDB(SessionBase):
    """Model for session data as stored in the database."""
    id: UUID = Field(..., description="Unique identifier for the session")
    created_at: datetime = Field(..., description="When the session was created")
    updated_at: datetime = Field(..., description="When the session was last updated")
    created_by: Optional[UUID] = Field(None, description="ID of the user who created the session")
    updated_by: Optional[UUID] = Field(None, description="ID of the user who last updated the session")

    model_config = {
        "from_attributes": True,  # Enables ORM mode for SQLAlchemy models
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "session_name": "my-session",
                "session_display_name": "My Session",
                "description": "A sample session",
                "engagement_id": "123e4567-e89b-12d3-a456-426614174000",
                "client_account_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_default": False,
                "session_type": "data_import",
                "status": "active",
                "auto_created": False,
                "metadata": {},
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "created_by": "123e4567-e89b-12d3-a456-426614174000",
                "updated_by": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    }


class Session(SessionInDB):
    """Session model for API responses."""
    pass


class SessionList(BaseModel):
    """Model for a list of sessions with pagination support."""
    items: List[Session] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")
    page: int = Field(1, description="Current page number")
    limit: int = Field(100, description="Number of items per page")
