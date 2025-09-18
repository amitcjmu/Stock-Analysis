"""
Master Flow Synchronization Service

This service ensures proper synchronization between master flows and child flows,
addressing Section 8 of the validation checklist:
- Status sync between master and child flows
- Progress percentage accuracy
- Phase transition logging
- Master flow orchestration integrity
"""

# Preserve backward compatibility by exposing the main classes
from .models import FlowSyncStatus, SyncResult
from .service import MasterFlowSyncService
from .mappers import FlowStatusMapper
from .database import FlowSyncDatabase

# Ensure all public API is available
__all__ = [
    "FlowSyncStatus",
    "SyncResult",
    "MasterFlowSyncService",
    "FlowStatusMapper",
    "FlowSyncDatabase",
]
