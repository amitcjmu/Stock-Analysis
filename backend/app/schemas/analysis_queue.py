"""
Pydantic schemas for analysis queue functionality.
"""

import enum
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class QueueStatus(str, enum.Enum):
    """Status of an analysis queue."""

    PENDING = "pending"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ItemStatus(str, enum.Enum):
    """Status of an item in the queue."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueueExportFormat(str, enum.Enum):
    """Export format options."""

    CSV = "csv"
    JSON = "json"


class AnalysisQueueCreate(BaseModel):
    """Request model for creating an analysis queue."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the analysis queue"
    )
    applicationIds: List[str] = Field(
        default_factory=list, description="List of application IDs to include"
    )


class AddItemRequest(BaseModel):
    """Request model for adding an item to a queue."""

    applicationId: str = Field(..., description="Application ID to add to the queue")


class AnalysisQueueItemResponse(BaseModel):
    """Response model for an analysis queue item."""

    id: str
    application_id: str
    status: ItemStatus
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalysisQueueResponse(BaseModel):
    """Response model for an analysis queue."""

    id: str
    name: str
    status: QueueStatus
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    items: Optional[List[AnalysisQueueItemResponse]] = None

    class Config:
        from_attributes = True
