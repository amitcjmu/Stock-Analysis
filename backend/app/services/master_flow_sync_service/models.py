"""
Data models for Master Flow Synchronization Service
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class FlowSyncStatus(BaseModel):
    """Status model for flow synchronization"""

    master_flow_id: UUID
    child_flow_id: UUID
    child_flow_type: str

    # Sync status
    is_synchronized: bool
    last_sync_at: Optional[datetime] = None

    # Status comparison
    master_status: str
    child_status: str
    status_match: bool

    # Progress comparison
    master_progress: float
    child_progress: float
    progress_diff: float

    # Phase tracking
    master_phase: Optional[str] = None
    child_phase: Optional[str] = None
    phase_match: bool

    # Issues found
    issues: List[str] = []
    recommendations: List[str] = []


class SyncResult(BaseModel):
    """Result model for synchronization operations"""

    success: bool
    flows_processed: int
    flows_synchronized: int
    issues_fixed: int

    # Details
    sync_statuses: List[FlowSyncStatus] = []
    errors: List[str] = []

    # Summary
    synchronized_at: datetime
    next_sync_recommended: Optional[datetime] = None
